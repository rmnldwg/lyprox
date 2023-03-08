"""
Module for translating the user input into a database query. It retrieves the
information of interest and returns it in a format that can then be put into the
response of the server.
"""
# pylint: disable=no-member, unused-argument

import logging
import re
import time
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from django.db.models import QuerySet

from accounts.models import Institution
from patients.models import Dataset, Diagnose, Patient, Tumor

logger = logging.getLogger(__name__)


def run_query(
    patients: QuerySet | None,
    cleaned_form_data: Dict[str, Any],
    do_compute_statistics: bool = True,
) -> Dict[int, Any]:
    """
    Run a database query using the cleaned form data from the
    `forms.DashboardForm`.

    It first filters all patients in the database by patient-specific
    characteristics. Then all tumors by tumor features. Afterwards, it only
    keeps those patients that have tumors which were not yet filtered out.
    It continues to remove patients based on their diagnosed lymph node
    involvement and the selected involvement patterns.
    """
    if patients is None:
        patients = Patient.objects.all()

    start_time = time.perf_counter()

    patients = patient_specific(patients, **cleaned_form_data)
    tumors = tumor_specific(Tumor.objects.all(), **cleaned_form_data)
    patients = patients.filter(tumor__in=tumors)
    diagnoses = Diagnose.objects.all().filter(patient__in=patients)

    # This is now a dictionary with exactly those patient's IDs who are
    # still not filtered out (after patient-, tumor- and diagnose-specific
    # filtering).
    combined_diagnoses_by_id = diagnose_specific(
        diagnoses, **cleaned_form_data
    )
    filtered_patient_ids = combined_diagnoses_by_id.keys()
    patients = patients.filter(id__in=filtered_patient_ids)
    tumors = tumors.filter(patient__id__in=filtered_patient_ids)

    if not do_compute_statistics:
        return patients, {}

    patients_by_id = sort_patients_by_id(patients.values())
    tumors_by_patient_id = sort_tumors_by_patient(tumors.values())

    try:
        info_by_id = collect_info(
            patients=patients_by_id,
            tumors=tumors_by_patient_id,
            diagnoses=combined_diagnoses_by_id,
        )
    except KeyError as key_err:
        logger.error("Most likely, different patient IDs were found in dicts.")
        raise KeyError from key_err

    statistics = compute_statistics(info_by_id)

    end_time = time.perf_counter()
    logger.info(
        "Entire query took %(time).3f s, returns %(count)d patients",
        {"time": end_time - start_time, "count": patients.count()},
    )

    return patients, statistics


def collect_info(
    patients: Dict[int, Any],
    tumors: Dict[int, Any],
    diagnoses: Dict[int, Any],
) -> Dict[int, Any]:
    """
    Collect the patient-, tumor-, and diagonse-information in one dictionary.

    Args:
        patients: Patients sorted by ID. Should be the output of `sort_patients_by_id`
        tumors: Tumors by patient ID, as returned by `sort_tumors_by_patient`
        diagnoses: Combined involvement by patient ID. Output of
            `sort_diagnoses_by_patient`.

    Returns:
        A dictionary with patient IDs as keys and the combined information underneath.
    """
    for id, patient in patients.items():
        patient["tumor"] = tumors[id]

        for side, side_diagnose in diagnoses[id].items():
            patient[side] = side_diagnose

    return patients


def compute_statistics(patients: Dict[int, Any]) -> Dict[str, Any]:
    """
    Use the collected information as returned by `collect_info` and generate
    statistics for them.
    """
    start_time = time.perf_counter()

    statistics = {   # initialize counts of patient- & tumor-related fields
        'total': len(patients),

        'datasets': {ds.id: 0 for ds in Dataset.objects.all()},

        'sex': np.zeros(shape=(3,), dtype=int),
        'nicotine_abuse': np.zeros(shape=(3,), dtype=int),
        'hpv_status': np.zeros(shape=(3,), dtype=int),
        'neck_dissection': np.zeros(shape=(3,), dtype=int),
        'n_status': np.zeros(shape=(3,), dtype=int),

        'subsites': np.zeros(shape=len(Tumor.SUBSITE_DICT), dtype=int),
        't_stages': np.zeros(shape=(len(Patient.T_stages),), dtype=int),
        'central': np.zeros(shape=(3,), dtype=int),
        'extension': np.zeros(shape=(3,), dtype=int),
    }
    for side in ['ipsi', 'contra']:
        for lnl in Diagnose.LNLs:
            statistics[f'{side}_{lnl}'] = np.zeros(shape=(3,), dtype=int)

    # loop through patients to populate the counts dictionary
    for id, patient in patients.items():
        statistics['datasets'][patient["dataset_id"]] += 1

        # PATIENT specific counts
        statistics['nicotine_abuse'] += tf2arr(patient["nicotine_abuse"])
        statistics['hpv_status'] += tf2arr(patient["hpv_status"])
        statistics['neck_dissection'] += tf2arr(patient["neck_dissection"])

        # TUMOR specific counts
        statistics['subsites'] += subsite2arr(patient["tumor"]["subsite"])
        statistics['t_stages'][patient["tumor"]["t_stage"]-1] += 1
        statistics['central'] += tf2arr(patient["tumor"]["central"])
        statistics['extension'] += tf2arr(patient["tumor"]["extension"])

        # N0/N+ counts
        has_ipsi = any(patient["ipsi"][lnl] for lnl in Diagnose.LNLs)
        has_contra = any(patient["contra"][lnl] for lnl in Diagnose.LNLs)

        if not has_ipsi and not has_contra:
            statistics['n_status'] += np.array([0,0,1])
        else:
            statistics['n_status'] += np.array([0,1,0])

        # DIAGNOSE specific (involvement) counts
        for side in ['ipsi', 'contra']:
            for lnl in Diagnose.LNLs:
                statistics[f'{side}_{lnl}'] += tf2arr(patient[side][lnl])

    statistics["datasets"] = [num for num in statistics["datasets"].values()]

    end_time = time.perf_counter()
    logger.info(
        "Statistics generation took %(time).3f s",
        {"time": end_time - start_time},
    )

    return statistics


def tf2arr(value):
    """
    Map ``True``, ``False`` & ``None`` to one-hot-arrays of length 3.

    This particular mapping comes from the fact that in the form ``True``, ``None``,
    ``False`` are represented by integers 1, 0, -1. So, the one-hot encoding uses an
    array of length 3 that is one only at these respective indices, where -1 is the
    last item.
    """
    if value is None:
        return np.array([1, 0, 0], dtype=int)
    else:
        if value:
            return np.array([0, 1, 0], dtype=int)
        else:
            return np.array([0, 0, 1], dtype=int)


def subsite2arr(subsite):
    """
    Map different subsites to an one-hot-array of subsite groups.

    E.g., a one in the first place means "base of tongue", at the second place is
    "tonsil" and so on.
    """
    res = np.zeros(shape=len(Tumor.SUBSITE_DICT), dtype=int)

    for i,subsite_list in enumerate(Tumor.SUBSITE_DICT.values()):
        if subsite in subsite_list:
            res[i] = 1

    if np.sum(res) > 1:
        logger.warning("Tumor associated with multiple subsites: %s", subsite)

    return res


def patient_specific(
    patients: Optional[QuerySet] = None,
    nicotine_abuse: Optional[bool] = None,
    hpv_status: Optional[bool] = None,
    neck_dissection: Optional[bool] = None,
    dataset__in: Optional[Institution] = None,
    **rest
) -> QuerySet:
    """
    Filter ``QuerySet`` of patients based on patient-specific properties.

    This function is designed in such a way that one can simply add another
    argument to its definition without actually changing the logic inside it
    and it will the be able to filter for that added argument (given that it
    is also a field in the model `patients.models.Patient`).

    Args:
        patients: The ``QuerySet`` of patients to begin with. I ``None``, this is just
            the entire patient dataset.
        nicotine_abuse: Filter smokers or non-smokers?
        hpv_status: Select based on HPV status.
        neck_dissection: Filter thos that did or didn't undergo neck dissection.
        dataset__in: Select based on the dataset that describes the respective patient.

    Returns:
        The filtered ``QuerySet``.
    """
    if patients is None:
        patients = Patient.objects.all()

    kwargs = locals()
    start_time = time.perf_counter()
    kwargs.pop('patients')
    kwargs.pop('rest')

    # the form fields are named such that they can be inserted into the
    # QuerySet filtering function directly
    for key, value in kwargs.items():
        if value is not None:
            patients = patients.filter(**{key: value})

    end_time = time.perf_counter()
    logger.info(
        "Patient query took %(time).3f s",
        {"time": end_time - start_time},
    )

    return patients


def sort_patients_by_id(patients: QuerySet) -> Dict[int, Any]:
    """Collect patient information by patient ID in a dictionary."""
    sorted_patients = {}
    for patient in patients:
        patient_id = patient.pop("id")
        sorted_patients[patient_id] = patient

    return sorted_patients


def tumor_specific(
    tumors: Optional[QuerySet] = None,
    subsite__in: Optional[List[str]] = None,
    t_stage__in: Optional[List[int]] = None,
    central: Optional[bool] = None,
    extension: Optional[bool] = None,
    **rest
) -> QuerySet:
    """
    Filter ``QuerySet`` of tumors based on tumor-specific properties.

    It works almost exactly like the patient-specific querying function
    `patient_specific` in terms of adding new arguments to filter by.

    Args:
        tumors: ``QuerySet`` of tumors to begin with. if ``None``, this simply
            includes all patients in the database.
        subsite__in: Is the tumor's subsite in this list of subsites?
        t_stage__in: Does the tumor's T-stage match one of this list?
        central: Is the tumor symmetric w.r.t. the mid-sagittal line?
        extension: Does the tumor extend over the mid-sagittal line?

    Returns:
        The ``QuerySet`` of tumors filtered for the requested characterisics.
    """
    if tumors is None:
        tumors = Tumor.objects.all()

    kwargs = locals()                     # extract keyword arguments and...
    start_time = time.perf_counter()
    kwargs.pop('tumors')                  # ...remove the tumor queryset and...
    kwargs.pop('rest')                    # ...any other kwargs from this dictionary.

    for key, value in kwargs.items():     # iterate over provided kwargs and ...
        if value is not None:             # ...if it's of interest, then filter
            tumors = tumors.filter(**{key: value})

    end_time = time.perf_counter()
    logger.info(
        "Tumor query took %(time).3f s",
        {"time": end_time - start_time},
    )

    return tumors


def sort_tumors_by_patient(tumors: QuerySet) -> Dict[int, Any]:
    """Collect tumor information by patient ID in a dictionary."""
    sorted_tumors = {}
    for tumor in tumors:
        patient_id = tumor.pop("patient_id")
        sorted_tumors[patient_id] = tumor

    return sorted_tumors


def diagnose_specific(
    diagnoses: QuerySet | None,
    modalities: List[int] | None,
    modality_combine: str = "maxLLH",
    n_status: bool | None = None,
    **kwargs,
) -> Dict[int, Dict[str, Dict[str, bool | None]]]:
    """
    Filter the diagnoses based on selected involvement patterns.

    In contrast to the `patient_specific` and `tumor_specific` functions, this one is
    more complicated: It needs to combine multiple modalities' information before
    checking if a patient's involvement matches the selected pattern.

    Args:
        diagnoses: ``QuerySet`` of diagnoses. If ``None``, all diagnose entries in the
            database will be used.
        modalities: List of diagnostic modalities to consider in the filtering.
        modality_combine: Name of the method to use for combining multiple, possibly
            conflicting diagnoses from different modalities.
        n_status: If ``True``, only patients will be kept that are N+ patients.
            ``False`` means only N0 patients are kept and ``None`` ignores N-status.

    Returns:
        A nested dictionary with patient IDs as top-level keys. Under each patient,
        there are the keys ``"ipsi"`` and ``"contra"``. And under that, finally, a
        dictionary stores the combined involvement (can be ``True`` for metastatic,
        ``False`` for healthy, or ``None`` for unknown) per LNL.
    """
    if diagnoses is None:
        diagnoses = Diagnose.objects.all()

    start_time = time.perf_counter()

    diagnoses = diagnoses.filter(modality__in=modalities)
    sorted_diagnoses = sort_diagnoses_by_patient(diagnoses)
    combined_diagnoses = combine_diagnoses(modality_combine, sorted_diagnoses)
    filter_pattern = extract_filter_pattern(kwargs)

    patient_ids_to_delete = []
    for patient_id, patient_diagnose in combined_diagnoses.items():
        if not does_patient_match(patient_diagnose, filter_pattern, n_status):
            patient_ids_to_delete.append(patient_id)

    for patient_id in patient_ids_to_delete:
        combined_diagnoses.pop(patient_id, None)

    end_time = time.perf_counter()
    logger.info(
        "Diagnose query took %(time).3f s",
        {"time": end_time - start_time},
    )

    return combined_diagnoses


def sort_diagnoses_by_patient(diagnoses: QuerySet) -> Dict[int, Dict[str, np.ndarray]]:
    """
    Use a ``QuerySet`` of `patient.models.Diagnose` and sort its entries into a
    nested dictionary.

    The top level of the dictionary has the patient's IDs as keys. Underneath it is
    sorted by side (``ipsi`` & ``contra``). The values of those are then `numpy`
    matrices that are indexed by modality and by LNL. They hold the involvement that
    was oserved by the corresponding modality for the respective LNL.

    Args:
        diagnoses: The ``QuerySet`` of diagnoses.

    Returns:
        The sorted, nested dictionary.
    """
    diagnoses = diagnoses.values()

    sorted_diagnoses = {}
    empty_diagnose_matrix = np.full(
        shape=(len(Diagnose.LNLs), len(Diagnose.Modalities)),
        fill_value=None,
    )
    modality_to_idx = {mod: i for i,mod in enumerate(Diagnose.Modalities.values)}

    for diagnose in diagnoses:
        if (patient_id := diagnose["patient_id"]) not in sorted_diagnoses:
            patient_diagnose = {}
        else:
            patient_diagnose = sorted_diagnoses[patient_id]

        if (side := diagnose["side"]) not in patient_diagnose:
            side_diagnose = empty_diagnose_matrix.copy()
        else:
            side_diagnose = patient_diagnose[side]

        modality_idx = modality_to_idx[diagnose["modality"]]

        for i,lnl in enumerate(Diagnose.LNLs):
            side_diagnose[i,modality_idx] = diagnose[lnl]

        patient_diagnose[side] = side_diagnose
        sorted_diagnoses[patient_id] = patient_diagnose

    return sorted_diagnoses


class ModalityCombinor:
    """
    Utility class that defines and helps to select the various methods for combining
    diagnoses from different modalities.
    """
    def __init__(self, method: str) -> None:
        """
        Initialize the helper class with the name of the method to combine modalities.
        """
        # pylint: disable=not-an-iterable
        self.method = method
        self.specificities = tuple(mod.spec for mod in Diagnose.Modalities)
        self.sensitivities = tuple(mod.sens for mod in Diagnose.Modalities)

    @staticmethod
    @lru_cache
    def logical_OR(
        values: Tuple[bool | None],
        specificities: Tuple[float],
        sensitivities: Tuple[float],
    ) -> bool:
        """Use the logical OR to determine combined involvement."""
        return any(values)

    @staticmethod
    @lru_cache
    def logical_AND(
        values: Tuple[bool | None],
        specificities: Tuple[float],
        sensitivities: Tuple[float],
    ) -> bool:
        """Logical AND combination method."""
        return any(not(v) if v is not None else None for v in values)

    @staticmethod
    @lru_cache
    def rank(
        values: Tuple[bool | None],
        specificities: Tuple[float],
        sensitivities: Tuple[float],
    ) -> bool:
        """
        Combine diagnoses by trusting the one with the highest spcificity/sensitivity.
        """
        healthy_sens = [
            sensitivities[i] for i,value in enumerate(values) if value is False
        ]
        involved_spec = [
            specificities[i] for i,value in enumerate(values) if value is True
        ]
        return np.max([*healthy_sens, 0.]) < np.max([*involved_spec, 0.])

    @staticmethod
    @lru_cache
    def max_llh(
        values: Tuple[bool | None],
        specificities: Tuple[float],
        sensitivities: Tuple[float],
    ) -> bool:
        """
        Combine diagnoses by computing true involvement is the most likely, given the
        provided set of observations.
        """
        healthy_llh = 1.
        involved_llh = 1.

        for value, spec, sens in zip(values, specificities, sensitivities):
            if value is None:
                continue
            if value:
                healthy_llh *= 1. - spec
                involved_llh *= sens
            else:
                healthy_llh *= spec
                involved_llh *= 1. - sens

        return healthy_llh < involved_llh

    def combine(self, values: Tuple[bool | None]) -> bool | None:
        """
        Choose the method to combine the diagnoses and perform the combination using
        the stored values for sensitivity and specificity.
        """
        if all(value is None for value in values):
            return None

        method_dict = {
            "OR": self.logical_OR,
            "AND": self.logical_AND,
            "rank": self.rank,
            "maxLLH": self.max_llh,
        }

        return method_dict[self.method](
            values, self.specificities, self.sensitivities
        )


def combine_diagnoses(
    method: Callable,
    diagnoses: Dict[int, Dict[str, np.ndarray]]
) -> Dict[int, Dict[str, Dict[str, bool | None]]]:
    """
    Combine the potentially conflicting diagnoses for each patient and each side
    according to the chosen combination method.

    Args:
        method: The function used to combine them. It should only take a tuple of
            values where each value represents the involvement for the same LNL as
            reported by the different modalities. The order of the values corresponds
            to the order of the modalities in `patients.models.Diagnose.Modalities`.
        diagnoses: This should be the output of the `sort_diagnoses` function.

    Returns:
        A dictionary where the combined involvement per LNL is stored under the
        corresponding patient ID, side (``ipsi`` or ``contra``) and the respective
        LNL's name (e.g. ``IIa``).
    """
    method = ModalityCombinor(method).combine
    combined_diagnoses = {}

    for patient_id, patient_diagnose in diagnoses.items():
        combined_diagnoses[patient_id] = {}
        for side in ["ipsi", "contra"]:
            if side not in patient_diagnose:
                combined_diagnoses[patient_id][side] = {
                    lnl: None for lnl in Diagnose.LNLs
                }
                continue

            side_diagnose = patient_diagnose[side]
            combined_diagnoses[patient_id][side] = {}
            for i,lnl in enumerate(Diagnose.LNLs):
                combined_diagnoses[patient_id][side][lnl] = method(
                    tuple(side_diagnose[i])
                )

    return combined_diagnoses


def extract_filter_pattern(
    kwargs: Dict[str, bool | None],
) -> Dict[str, Dict[str, bool | None]]:
    """
    Sort the ``kwargs`` from the request.

    The filter patterns are sent in the request (e.g. as ``{ipsi_IIa: True}``). This
    method sorts them into a dictionary by side (``ipsi`` or ``contra``) and by LNL.
    """
    filter_pattern = {"ipsi": {}, "contra": {}}
    for key, value in kwargs.items():
        pattern = r"(ipsi|contra)_([IVX]{1,3}[ab]?)"
        if (match := re.match(pattern, key)) is not None:
            filter_pattern[match[1]][match[2]] = value

    return filter_pattern


def does_patient_match(
    patient_diagnose: Dict[str, Dict[str, bool | None]],
    filter_pattern: Dict[str, Dict[str, bool | None]],
    n_status: bool | None,
) -> bool:
    """
    Compare the diagnose of a patient with the involvement pattern to filter for.

    A 'match' occurs, when for both sides (``ipsi`` & ``contra``)
    and all LNLs the patient's diagnose and the ``filter_pattern`` are the same or the
    latter is undefined (``None``).

    Args:
        patient_diagnose: The diagnose of a single patient, as they are stored by their
            IDs in the output of the `combine_diagnoses` dictionary.
        filter_pattern: The involvement pattern that was selected in the `dashboard`
            by the user, collected in the same format as the ``patient_diagnose``.
        n_status: If ``True``, only patients will be kept that are N+ patients.
            ``False`` means only N0 patients are kept and ``None`` ignores N-status.

    Returns:
        Whether ``patient_diagnose`` and ``filter_pattern`` match or not.
    """
    is_n_plus = False
    for side, side_diagnose in patient_diagnose.items():
        for lnl, lnl_diagnose in side_diagnose.items():
            is_n_plus = True if lnl_diagnose is True else is_n_plus
            if n_status is False and lnl_diagnose is True:
                return False
            if (lnl_pattern := filter_pattern[side][lnl]) is None:
                continue
            if lnl_pattern != lnl_diagnose:
                return False

    if n_status is True:
        return is_n_plus

    return True

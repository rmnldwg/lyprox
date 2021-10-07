from django.db.models import Q, F, QuerySet

import numpy as np
import logging
from typing import Optional, List, Dict, Tuple, Any

from patients.models import Patient, Diagnose, Tumor
from accounts.models import Institution

logger = logging.getLogger(__name__)


def tf2arr(value: Optional[bool]) -> np.ndarray:
    """Map `True`, `False` & `None` to required format for counting the 
    occurrences.
    
    Args:
        value: The value to be transformed into the one-hot encoding.
    
    Returns:
        A one-hot encoding in the form of an array with length 3. The first 
        element (index 0) corresponds to a ``value`` of ``None``. The second 
        element (index 1) to a ``value`` of ``True`` (1 <-> ``True``, that 
        is the logic behind the choice of this encoding) and the third and last 
        element (index -1) to a ``value`` of ``False`` (-1 <-> ``False``).
    """
    if value is None:
        return np.array([1, 0, 0], dtype=int)
    else:
        if value:
            return np.array([0, 1, 0], dtype=int)
        else:
            return np.array([0, 0, 1], dtype=int)    
        
        
def subsite2arr(subsite: str) -> np.ndarray:
    """Map ICD codes for primary tumor subsites to required format for counting 
    the occurrences.
    
    Args:
        subsite: IDC code for the specific tumor subsite.
    
    Returns:
        A one-hot encoding in the form of an array with length 3. The first 
        element corresponds to the subsite "base of tongue", the second to 
        "tonsil" and the last to any other subsite.
    """
    if subsite in ["C01.9"]:
        return np.array([1, 0, 0], dtype=int)
    elif subsite in ["C09.0", "C09.1", "C09.8", "C09.9"]:
        return np.array([0, 1, 0], dtype=int)
    else:
        return np.array([0, 0, 1], dtype=int)
    
    
def side2arr(side: str) -> np.ndarray:
    """Map the side of the primary tumor to a one-hot encoding of length three.
    
    Args:
        side: Lateralization of the tumor.
    
    Returns:
        A one-hot encoding of the different sides: The array has a one at index 
        0 if the lateralization is unknown, at index 1 if it is known and 
        lateralized and at index -1 if it is not lateralized.
    """
    if side == "central":
        return np.array([0, 1, 0], dtype=int)
    elif (side == "left") or (side == "right"):
        return np.array([0, 0, 1], dtype=int)
    else:
        return np.array([1, 0, 0], dtype=int)



def patient_specific(
    patient_queryset: QuerySet,
    nicotine_abuse: Optional[bool] = None,
    hpv_status: Optional[bool] = None,
    neck_dissection: Optional[bool] = None,
    institution__in: Optional[List[Institution]] = None,
    **rest
) -> QuerySet:
    """Filter patients based on person-specific characteristics.
    
    Args:
        patient_queryset: The :class:`QuerSey` of :class:`patients.models.Patient` 
            instances that is to be filtered.
        nicotine_abuse: Filter for patients that are/were smokers (``True``) or 
            non-smoking persons (``False``). Ignore if set to ``None``.
        hpv_status: In- or exclude depending on HPV status: If ``True``, only
            patients that are HPV positive are included, when set to ``False`` 
            HPV negative patients are included and if set to ``None``, no 
            selection is made w.r.t. HPV.
        neck_dissection: Choose patients that have undergone neck dissection 
            (``True``) or not (``False``). Ignore this attribute if set to 
            ``None``.
        institution__in: List of institutions the patients can come from. If 
            the patient's institution is not in the list, they are excluded. 
            This parameter's naming is chosen such that it can, as a ``kwarg``, 
            be inserted into the QuerySet's ``filter`` function directly.
    
    Returns:
        The filtered set of patients.
    """
    kwargs = locals()
    kwargs.pop('patient_queryset')
    kwargs.pop('rest')
    
    # the form fields are named such that they can be inserted into the 
    # QuerySet filtering function directly
    for key, value in kwargs.items():
        if value is not None:
            patient_queryset = patient_queryset.filter(**{key: value})
    
    return patient_queryset


def tumor_specific(
    patient_queryset: QuerySet,
    subsite__in: List[str] = [
        "C01.9",
        "C09.0", "C09.1", "C09.8", "C09.9",
        "C10.0", "C10.1", "C10.2", "C10.3", "C10.4", 
        "C10.8", "C10.9", "C12.9", "C13.0", "C13.1", 
        "C13.2", "C13.8", "C13.9", "C32.0", "C32.1", 
        "C32.2", "C32.3", "C32.8", "C32.9"
    ],
    t_stage__in: List[int] = [1,2,3,4],
    side__in: List[str] = ['left', 'right', 'central'],
    extension: Optional[bool] = None,
    **rest
) -> QuerySet:
    """Filter patients based on characteristics of their tumors.
    
    Args:
        patient_queryset: The :class:`QuerSey` of :class:`patients.models.Patient` 
            instances that is to be filtered.
        subsite__in: List of subsites the primary tumor should be in. Nameing 
            of this parameter is chosen such that it can be inserted into the 
            QuerSet's ``filter`` fuction directly as a ``kwarg``.
        t_stage__in: List of T-stages the tumor can be in. Naming like for the 
            ``subsite__in`` parameter.
        side__in: Lateralizations that can be included in the final QuerySet.
        extension: Filter patients based on whether their tumor extends over 
            the mid-sagittal extension or not.
    
    Returns:
        The filtered set of patients.
    """
    kwargs = locals()              # extract keyword arguments and...
    kwargs.pop('patient_queryset') # ...remove the patient queryset and...
    kwargs.pop('rest')             # ...any other kwargs from this dictionary.
    for key, value in kwargs.items():   # iterate over provided kwargs and ...
        if value is not None:             # ...if it's of interest, then filter
            patient_queryset = patient_queryset.filter(**{f'tumor__{key}': value})
    
    return patient_queryset


def diagnose_specific(
    patient_queryset: QuerySet,
    cleaned_data: Dict[str, Any],
    assign_central: str = "left",
) -> Tuple[QuerySet, QuerySet]:
    """Filter patients based on a pattern of lymphatic involvement that should 
    match the combination of the selected diagnostc modalities available.
    
    Args:
        patient_queryset: The :class:`QuerSey` of :class:`patients.models.Patient` 
            instances that is to be filtered.
        cleaned_data: The cleaned data from the :class:`dashboard.forms.DashboardForm`. 
            The function extracts the pattern of nodal involvement from this 
            dictionary.
        assign_central: For patients with a central tumor, assign this side to 
            be the ipsilateral one.
    
    Returns:
        The filtered QuerySet, as well as the respective QuerySet of diagnoses.
    """
    # DIAGNOSES
    d = Diagnose.objects.all().filter(patient__in=patient_queryset,
                                      modality__in=cleaned_data['modalities'])
    q_ipsi = (Q(side=F("patient__tumor__side"))
              | (Q(patient__tumor__side="central")
                 & Q(side=assign_central)))
    
    diagnose_querysets = {
        'ipsi'  : d.filter(q_ipsi).select_related('patient').values(),
        'contra': d.exclude(q_ipsi).select_related('patient').values()
    }
    
    diagnose_tables = {
        'ipsi'  : {},
        'contra': {}
    }
    
    patient_queryset = patient_queryset.filter(
        Q(diagnose__in=d.filter(q_ipsi)) | Q(diagnose__in=d.exclude(q_ipsi))
    ).distinct()
    
    selected_diagnose = {    # via form selected diagnoses will be stored here
        'ipsi'  : np.array([None] * len(Diagnose.LNLs)),
        'contra': np.array([None] * len(Diagnose.LNLs))
    }
    
    # sort diags into patient bins...
    combined_involvement = {'ipsi'  : {},
                            'contra': {}}
    for side in ['ipsi', 'contra']:
        for i,lnl in enumerate(Diagnose.LNLs):
            if (selected_inv := cleaned_data[f'{side}_{lnl}']) is not None:
                selected_diagnose[side][i] = selected_inv
                
        for diagnose in diagnose_querysets[side]:
            patient_id = diagnose['patient_id']
            # note the double square brackets below to make sure the 
            # `diag_array` is two-dimensional. Without it, the 
            # `np.all(, axis=0)` below would not work properly.
            diag_array = np.array([[diagnose[f'{lnl}'] for lnl in Diagnose.LNLs]])
            
            try:
                diagnose_tables[side][patient_id] = np.vstack([
                    diagnose_tables[side][patient_id],
                    diag_array
                ])
            except KeyError:
                diagnose_tables[side][patient_id] = diag_array
        
        # ...and aggregate/combine each patient's diag    
        for pat_id, diag_table in diagnose_tables[side].items():
            if cleaned_data['modality_combine'] == 'OR':
                combine = any
            elif cleaned_data['modality_combine'] == 'AND':
                combine = all
            else:
                msg = ("Modalities can only be combined using logical OR or "
                       "logical AND")
                logger.error(msg)
                raise ValueError(msg)
            
            try:
                combined_involvement[side][pat_id] = np.array(
                    [combine(col) for col in diag_table.T],
                    dtype=object
                )
            except TypeError:  # difference: square bracket around `col`
                combined_involvement[side][pat_id] = np.array(
                    [combine([col]) for col in diag_table.T],
                    dtype=object
                )
            # when all observations yield 'unknown' for a LNL, report 'unknown'
            all_none_idx = np.all(diag_table == None, axis=0)
            combined_involvement[side][pat_id][all_none_idx] = None
            
            mask = selected_diagnose[side] != None
            match = np.all(np.equal(combined_involvement[side][pat_id], 
                                    selected_diagnose[side],
                                    where=mask,
                                    out=np.ones_like(mask, dtype=bool)))
            if not match:   # if it does not match, remove patient from queryset
                patient_queryset = patient_queryset.exclude(id=pat_id)
    
    return patient_queryset, combined_involvement


def n_zero_specific(
    patient_queryset: QuerySet,
    combined_involvement: Dict[str, Dict[str, np.ndarray]],
    n_status: Optional[bool] = None
):
    """Filter for N+ or N0. ``n_status`` is ``True`` when we only want to see N+ 
    patients and ``False`` when we only want to see N0 patients.
    """
    if n_status is None:
        return patient_queryset, combined_involvement
    
    patients = patient_queryset.values("id")
    for pat in patients:
        pat_id = pat["id"]
        try:
            has_ipsi_inv = any(combined_involvement["ipsi"][pat_id])
        except KeyError:
            has_ipsi_inv = False
        
        try:
            has_contra_inv = any(combined_involvement["contra"][pat_id])
        except KeyError:
            has_contra_inv = False
        
        if n_status and not (has_ipsi_inv or has_contra_inv):
            patient_queryset = patient_queryset.exclude(id=pat_id)
        elif not n_status and (has_ipsi_inv or has_contra_inv):
            patient_queryset = patient_queryset.exclude(id=pat_id)
    
    return patient_queryset, combined_involvement


def count_patients(
    patient_queryset: QuerySet,
    combined_involvement: Dict[str, Dict[str, np.ndarray]]
):
    """Count how often patients have various characteristics like HPV status, 
    certain lymph node level involvement, and so on.
    """
    # prefetch patients and important fields for performance
    patients = patient_queryset.prefetch_related('tumor_set')
    counts = {   # initialize counts of patient- & tumor-related fields
        'total': len(patients),
        
        'gender': np.zeros(shape=(3,), dtype=int),
        'nicotine_abuse': np.zeros(shape=(3,), dtype=int),
        'hpv_status': np.zeros(shape=(3,), dtype=int),
        'neck_dissection': np.zeros(shape=(3,), dtype=int),
        'n_zero': np.zeros(shape=(3,), dtype=int),
        
        'subsites': np.zeros(shape=(3,), dtype=int),
        't_stages': np.zeros(shape=(len(Patient.T_stages),), dtype=int),
        'central': np.zeros(shape=(3,), dtype=int),
        'extension': np.zeros(shape=(3,), dtype=int), 
    }
    for side in ['ipsi', 'contra']:
        for lnl in Diagnose.LNLs:
            counts[f'{side}_{lnl}'] = np.zeros(shape=(3,), dtype=int)
            
    # loop through patients to populate the counts dictionary
    for patient in patients:
        # PATIENT specific counts
        counts['nicotine_abuse'] += tf2arr(patient.nicotine_abuse)
        counts['hpv_status'] += tf2arr(patient.hpv_status)
        counts['neck_dissection'] += tf2arr(patient.neck_dissection)
        
        # TUMOR specific counts
        tumor = patient.tumor_set.first()
        counts['subsites'] += subsite2arr(tumor.subsite)
        counts['t_stages'][tumor.t_stage-1] += 1
        counts['central'] += side2arr(tumor.side)
        counts['extension'] += tf2arr(tumor.extension)
        
        # N0/N+ counts
        has_contra = np.any(combined_involvement["contra"][patient.id])
        has_ipsi = np.any(combined_involvement["ipsi"][patient.id])
        if not has_ipsi and not has_contra:
            counts['n_zero'] += np.array([0,0,1])
        else:
            counts['n_zero'] += np.array([0,1,0])
        
        # DIAGNOSE specific (involvement) counts
        for side in ['ipsi', 'contra']:
            for i,lnl in enumerate(Diagnose.LNLs):
                try:
                    tmp = combined_involvement[side][patient.id][i]
                except KeyError:
                    # Not all patients have necessarily symmetric diagnoses, 
                    # which my code takes care of in the `diagnose_specific` 
                    # function, but not here, which is why this try is needed.
                    pass
                counts[f'{side}_{lnl}'] += tf2arr(tmp)
                
    return patient_queryset, counts
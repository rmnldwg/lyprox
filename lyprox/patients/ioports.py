"""
Module for importing and exporting CSV tables of patients with lymphatic
patterns of progression into and from the Django database.
"""
# pylint: disable=no-member
# pylint: disable=logging-fstring-interpolation

from __future__ import annotations

import logging
import warnings
from typing import List, Tuple

import numpy as np
import pandas as pd
from django.db.models import QuerySet

from . import models

logger = logging.getLogger(__name__)
warnings.simplefilter(action="ignore", category=pd.errors.PerformanceWarning)


class ParsingError(Exception):
    """
    Exception raised when the parsing of an uploaded CSV fails due to
    missing data columns.
    """


def compute_hash(*args):
    """
    Compute a hash vlaue from three patient-specific fields that must be
    removed due for respecting the patient's privacy.
    """
    return hash(args)


def nan_to_none(sth):
    """Transform NaNs to ``None``."""
    if sth != sth:
        return None
    else:
        return sth


def get_model_fields(model, remove: List[str] = None):
    """
    Get list of names of model fields and remove the ones provided via the
    ``remove`` argument.
    """
    fields = model._meta.get_fields()
    field_names = [f.name for f in fields]

    if remove is None:
        remove = []

    for entry in remove:
        try:
            field_names.remove(entry)
        except ValueError:
            pass

    return field_names


def row2patient(row, dataset):
    """
    Create a `Patient` instance from a row of a ``DataFrame`` containing the
    appropriate information, as well as the dataset in which the information was
    uploaded.
    """
    patient_dict = row.to_dict()
    _ = nan_to_none

    patient_fields = get_model_fields(
        models.Patient, remove=[
            "id", "tumor", "t_stage", "stage_prefix",
            "diagnose", "dataset"
        ]
    )

    valid_patient_dict = {}
    for field in patient_fields:
        try:
            valid_patient_dict[field] = _(patient_dict[field])
        except KeyError:
            logger.warning(f"Missing column {field} in table for importing patient.")

    new_patient = models.Patient(
        dataset=dataset,
        **valid_patient_dict
    )
    new_patient.save()
    return new_patient


def row2tumors(row, patient):
    """
    Create `Tumor` instances from row of a ``DataFrame`` and add them to an
    existing `Patient` instance.
    """
    # extract number of tumors in row
    level_zero = row.index.get_level_values(0)
    num_tumors = np.max([int(num) for num in level_zero])
    _ = nan_to_none

    tumor_fields = get_model_fields(
        models.Tumor, remove=["id", "patient"]
    )

    for i in range(num_tumors):
        tumor_dict = row[(f"{i+1}")].to_dict()

        valid_tumor_dict = {}
        for field in tumor_fields:
            try:
                valid_tumor_dict[field] = _(tumor_dict[field])
            except KeyError:
                logger.warning(f"Missing column {field} in table for importing tumor.")

        new_tumor = models.Tumor(
            patient=patient,
            **valid_tumor_dict
        )
        new_tumor.save()


def row2diagnoses(row, patient):
    """
    Create `Diagnose` instances from row of ``DataFrame`` and add them to an
    existing `Patient` instance.
    """
    modalities_list = list(set(row.index.get_level_values(0)))
    if len(modalities_list) == 0:
        raise ParsingError(
            "No diagnostic modalities were found in the provided table."
        )

    _ = nan_to_none

    diagnose_fields = get_model_fields(
        models.Diagnose, remove=["id", "patient", "modality", "side", "diagnose_date"]
    )

    modalities_intersection = list(
        set(modalities_list) & set(models.Diagnose.Modalities.values)
    )

    for mod in modalities_intersection:
        diagnose_date = _(row[(mod, "info", "date")])
        if diagnose_date is not None:
            for side in ["ipsi", "contra"]:
                diagnose_dict = row[(mod, side)].to_dict()

                valid_diagnose_dict = {}
                for field in diagnose_fields:
                    try:
                        valid_diagnose_dict[field] = _(diagnose_dict[field])
                    except KeyError:
                        logger.debug(
                            f"Column {field} not in table of modality {mod}, "
                            "setting to `None`."
                        )
                        valid_diagnose_dict[field] = None

                new_diagnosis = models.Diagnose(
                    patient=patient, modality=mod, side=side,
                    diagnose_date=diagnose_date,
                    **valid_diagnose_dict
                )
                new_diagnosis.save()


def import_from_pandas(
    data_frame: pd.DataFrame,
    dataset: models.Dataset,
    anonymize: List[str] = None
) -> Tuple[int]:
    """Import patients from pandas ``DataFrame``."""
    num_new = 0
    num_skipped = 0

    if anonymize is None:
        anonymize = ["id"]

    for _, row in data_frame.iterrows():
        # Make sure first two levels are correct for patient data
        try:
            patient_row = row[("patient", "#")]
        except KeyError as key_err:
            raise ParsingError(
                "For patient info, first level must be 'patient', second level "
                "must be '#'."
            ) from key_err

        new_patient = row2patient(patient_row, dataset=dataset)

        # make sure first level is correct for tumor
        try:
            tumor_row = row[("tumor")]
        except KeyError as key_err:
            raise ParsingError(
                "For tumor info, first level must be 'tumor' and second level "
                "must be number of tumor."
            ) from key_err

        row2tumors(
            tumor_row, new_patient
        )

        not_patient = row.index.get_level_values(0) != "patient"
        not_tumor = row.index.get_level_values(0) != "tumor"
        row2diagnoses(
            row.loc[not_patient & not_tumor], new_patient
        )

        num_new += 1

    return num_new, num_skipped


def export_to_pandas(patients: QuerySet):
    """
    Export ``QuerySet`` of patients into a pandas ``DataFrame`` of the same
    format as it is needed for importing.
    """
    # create list of tuples for MultiIndex and use that to create DataFrame
    patient_fields = get_model_fields(
        models.Patient, remove=["hash_value", "tumor", "diagnose", "t_stage"]
    )
    patient_column_tuples = [("patient", "#", f) for f in patient_fields]

    num_tumors = np.max([pat.tumor_set.all().count() for pat in patients])
    tumor_fields = get_model_fields(
        models.Tumor, remove=["id", "patient"]
    )
    tumor_column_tuples = []
    for field in tumor_fields:
        for i in range(num_tumors):
            tumor_column_tuples.append(("tumor", f"{i+1}", field))

    diagnose_fields = get_model_fields(
        models.Diagnose, remove=["id", "patient", "modality", "side", "diagnose_date"]
    )
    diagnose_column_tuples = []
    for mod in models.Diagnose.Modalities.values:
        diagnose_column_tuples.append((mod, "info", "date"))
        for side in ["ipsi", "contra"]:
            for field in diagnose_fields:
                diagnose_column_tuples.append((mod, side, field))

    tuples = [*patient_column_tuples,
              *tumor_column_tuples,
              *diagnose_column_tuples]
    columns = pd.MultiIndex.from_tuples(tuples)

    # prefetch fields for performance
    patients = patients.prefetch_related("tumor_set", "diagnose_set")

    # loop through patients
    list_of_rows = []
    for patient in patients:
        new_row = {}

        for field in patient_fields:
            new_row[("patient", "#", field)] = getattr(patient, field)

        for t,tumor in enumerate(patient.tumor_set.all()):
            for field in tumor_fields:
                new_row[("tumor", f"{t+1}", field)] = getattr(tumor, field)

        for diagnose in patient.diagnose_set.all():
            mod = diagnose.modality
            side = diagnose.side
            new_row[(mod, "info", "date")] = diagnose.diagnose_date
            for field in diagnose_fields:
                new_row[(mod, side, field)] = getattr(diagnose, field)

        list_of_rows.append(new_row)

    return pd.DataFrame(list_of_rows, columns=columns)

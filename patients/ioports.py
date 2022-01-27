import logging
from typing import List

import numpy as np
import pandas as pd
from django.db import IntegrityError
from django.db.models import QuerySet

logger = logging.getLogger(__name__)

from .models import Diagnose, Patient, Tumor


class ParsingError(Exception):
    """Exception raised when the parsing of an uploaded CSV fails due to
    missing data columns.
    """


def compute_hash(*args):
    """Compute a hash vlaue from three patient-specific fields that must be
    removed due for respecting the patient's privacy."""
    return hash(args)


def nan_to_None(sth):
    if sth != sth:
        return None
    else:
        return sth


def get_model_fields(model, remove: List[str] = []):
    """Get list of names of model fields and remove the ones provided via the
    `remove` argument."""
    fields = model._meta.get_fields()
    field_names = [f.name for f in fields]
    for entry in remove:
        try:
            field_names.remove(entry)
        except ValueError:
            pass

    return field_names


def row2patient(row, user, anonymize: List[str]):
    """Create a `Patient` instance from a row of a `DataFrame` containing the
    appropriate information, as well as the user that uploaded the information.
    """
    patient_dict = row.to_dict()
    _ = nan_to_None

    if len(anonymize) != 0:
        to_hash = [patient_dict.pop(a) for a in anonymize]
        hash_value = compute_hash(*to_hash)
    else:
        hash_value = compute_hash(*patient_dict)

    patient_fields = get_model_fields(
        Patient, remove=[
            "id", "hash_value", "tumor", "t_stage", "stage_prefix",
            "diagnose", "institution"
        ]
    )

    valid_patient_dict = {}
    for field in patient_fields:
        try:
            valid_patient_dict[field] = _(patient_dict[field])
        except KeyError:
            raise ParsingError(f"Column {field} is missing")

    try:
        new_patient = Patient(
            hash_value=hash_value,
            institution=user.institution,
            **valid_patient_dict
        )
        new_patient.save()
    except IntegrityError as ie:
        msg = ("Hash value already in database. Patient might have been added "
               "before")
        logger.warn(msg)
        raise ie

    return new_patient


def row2tumors(row, patient):
    """Create `Tumor` instances from row of a `DataFrame` and add them to an
    existing `Patient` instance."""
    # extract number of tumors in row
    level_zero = row.index.get_level_values(0)
    num_tumors = np.max([int(num) for num in level_zero])
    _ = nan_to_None

    tumor_fields = get_model_fields(
        Tumor, remove=["id", "patient"]
    )

    for i in range(num_tumors):
        tumor_dict = row[(f"{i+1}")].to_dict()

        valid_tumor_dict = {}
        for field in tumor_fields:
            try:
                valid_tumor_dict[field] = _(tumor_dict[field])
            except KeyError:
                raise ParsingError(f"Columns {field} is missing.")

        new_tumor = Tumor(
            patient=patient,
            **valid_tumor_dict
        )
        new_tumor.save()


def row2diagnoses(row, patient):
    """Create `Diagnose` instances from row of `DataFrame` and add them to an
    existing `Patient` instance."""
    modalities_list = list(set(row.index.get_level_values(0)))
    if len(modalities_list) == 0:
        raise ParsingError(
            "No diagnostic modalities were found in the provided table."
        )

    _ = nan_to_None

    diagnose_fields = get_model_fields(
        Diagnose, remove=["id", "patient", "modality", "side", "diagnose_date"]
    )

    modalities_intersection = list(
        set(modalities_list) & set(Diagnose.Modalities.values)
    )

    for mod in modalities_intersection:
        diagnose_date = _(row[(mod, "info", "date")])
        if diagnose_date is not None:
            for side in ["left", "right"]:
                diagnose_dict = row[(mod, side)].to_dict()

                valid_diagnose_dict = {}
                for field in diagnose_fields:
                    try:
                        valid_diagnose_dict[field] = _(diagnose_dict[field])
                    except KeyError:
                        raise ParsingError(f"Column {field} is missing.")

                new_diagnosis = Diagnose(
                    patient=patient, modality=mod, side=side,
                    diagnose_date=diagnose_date,
                    **valid_diagnose_dict
                )
                new_diagnosis.save()


def import_from_pandas(
    data_frame: pd.DataFrame,
    user,
    anonymize: List[str] = ["id"]
):
    """Import patients from pandas `DataFrame`."""
    num_new = 0
    num_skipped = 0

    for i, row in data_frame.iterrows():
        # Make sure first two levels are correct for patient data
        try:
            patient_row = row[("patient", "#")]
        except KeyError:
            raise ParsingError(
                "For patient info, first level must be 'patient', second level "
                "must be '#'."
            )

        # skip row if patient is already in database
        try:
            new_patient = row2patient(
                patient_row, user=user, anonymize=anonymize
            )
        except IntegrityError:
            msg = ("Skipping row")
            logger.warn(msg)
            num_skipped += 1
            continue

        # make sure first level is correct for tumor
        try:
            tumor_row = row[("tumor")]
        except KeyError:
            raise ParsingError(
                "For tumor info, first level must be 'tumor' and second level "
                "must be number of tumor."
            )

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
    """Export `QuerySet` of patients into a pandas `DataFrame` of the same
    format as it is needed for importing."""

    # create list of tuples for MultiIndex and use that to create DataFrame
    patient_fields = get_model_fields(
        Patient, remove=["hash_value", "tumor", "diagnose", "t_stage"]
    )
    patient_column_tuples = [("patient", "#", f) for f in patient_fields]

    num_tumors = np.max([pat.tumor_set.all().count() for pat in patients])
    tumor_fields = get_model_fields(
        Tumor, remove=["id", "patient"]
    )
    tumor_column_tuples = []
    for field in tumor_fields:
        for i in range(num_tumors):
            tumor_column_tuples.append(("tumor", f"{i+1}", field))

    diagnose_fields = get_model_fields(
        Diagnose, remove=["id", "patient", "modality", "side", "diagnose_date"]
    )
    diagnose_column_tuples = []
    for mod in Diagnose.Modalities.values:
        diagnose_column_tuples.append((mod, "info", "date"))
        for side in ["left", "right"]:
            for field in diagnose_fields:
                diagnose_column_tuples.append((mod, side, field))

    tuples = [*patient_column_tuples,
              *tumor_column_tuples,
              *diagnose_column_tuples]
    columns = pd.MultiIndex.from_tuples(tuples)
    df = pd.DataFrame(columns=columns)

    # prefetch fields for performance
    patients = patients.prefetch_related("tumor_set", "diagnose_set")

    # loop through patients
    for patient in patients:
        new_row = {}

        for field in patient_fields:
            new_row[("patient", "#", field)] = getattr(patient, field)

        for t,tumor in enumerate(patient.tumor_set.all()):
            for field in tumor_fields:
                new_row[("tumor", f"{t+1}", field)] = getattr(tumor, field)

        for diagnose in patient.diagnose_set.all():
            mod = Diagnose.Modalities(diagnose.modality).value
            side = diagnose.side
            new_row[(mod, "info", "date")] = diagnose.diagnose_date
            for field in diagnose_fields:
                new_row[(mod, side, field)] = getattr(diagnose, field)

        df = df.append(new_row, ignore_index=True)

    return df
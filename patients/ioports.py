from django.db import IntegrityError
from django.db.models import QuerySet

import numpy as np
import pandas as pd
from typing import List, Tuple
import logging
logger = logging.getLogger(__name__)

from .models import (Patient, Diagnose, Tumor)
from accounts.models import User


class ParsingError(Exception):
    """Exception raised when the parsing of an uploaded CSV fails due to 
    missing data columns."""
    
    def __init__(self, column, message="Missing column in uploaded table"):
        self.column = column
        self.message = message
        super().__init__(self.message)
    
    def __str__(self):
        return f"{self.column}: {self.message}"


def compute_hash(*args):
    """Compute a hash vlaue from three patient-specific fields that must be 
    removed due for respecting the patient's privacy."""
    return hash(args)


def nan_to_None(sth):
    """Converts ``NaN`` from the pabdas table to pythonic ``None``."""
    if sth != sth:
        return None
    else:
        return sth


def get_model_fields(model, remove: List[str] = []) -> List[str]:
    """Get list of names of model fields and remove the ones provided via the
    ``remove`` argument."""
    fields = model._meta.get_fields()
    field_names = [f.name for f in fields]
    for entry in remove:
        try:
            field_names.remove(entry)
        except ValueError:
            pass
    
    return field_names


def row2patient(row: pd.Series, user: User, anonymize: List[str]) -> Patient:
    """Create a patient from a row of a table.
    
    Args:
        row: The row of the :class:`pd.DataFrame` table.
        user: The currently logged in user that will pass on their institution 
            to the newly created :class:`Patient`
        anonymize: List of fields used to anonymize the patient by computing a 
            hash from the content of those fields.
    
    Returns:
        The patient created from the row of a table.
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
            "id", "hash_value", "tumor", "diagnose", "t_stage", "institution"
        ]
    )
    
    valid_patient_dict = {}
    for field in patient_fields:
        try:
            valid_patient_dict[field] = _(patient_dict[field])
        except KeyError:
            column = field
            raise ParsingError(column)
    
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


def row2tumors(row: pd.Series, patient: Patient) -> Tumor:
    """Create a new tumor from a table row and connect it to an already created 
    patient.
    
    Args:
        row: The row of the :class:`pd.DataFrame` table.
        patient: A previously created patient who's tumor is created in this 
            function.
    
    Returns:
        The patient's tumor, extracted from a table row.
    
    See Also:
        :func:`row2diagnoses`: Same function, but for a diagnose instead of a 
            tumor.
    """
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
                column = field
                raise ParsingError(column)
        
        new_tumor = Tumor(
            patient=patient,
            **valid_tumor_dict
        )
        new_tumor.save()


def row2diagnoses(row: pd.Series, patient: Patient) -> Diagnose:
    """Create a new diagnose from a table row and connect it to an already 
    created patient.
    
    Args:
        row: The row of the :class:`pd.DataFrame` table.
        patient: A previously created patient who's diagnose is created in this 
            function.
    
    Returns:
        The patient's diagnose, extracted from a table row.
        
    See Also:
        :func:`row2tumors`: Same function, but for a tumor instead of a 
            diagnose.
    """
    modalities_list = list(set(row.index.get_level_values(0)))
    if not set(modalities_list).issubset(Diagnose.Modalities.labels):
        message = ("Unknown diagnostic modalities were provided. Known are "
                   f"only {Diagnose.Modalities.labels}.")
        raise ParsingError(column="Modalities", message=message)
    
    if len(modalities_list) == 0:
        message = "No diagnostic modalities were found in the provided table."
        raise ParsingError(column="Modalities", message=message)
    
    _ = nan_to_None
    
    diagnose_fields = get_model_fields(
        Diagnose, remove=["id", "patient", "modality", "side", "diagnose_date"]
    )
    
    for mod in modalities_list:
        diagnose_date = _(row[(mod, "info", "date")])
        if diagnose_date is not None:
            for side in ["left", "right"]:
                diagnose_dict = row[(mod, side)].to_dict()
                
                valid_diagnose_dict = {}
                for field in diagnose_fields:
                    try:
                        valid_diagnose_dict[field] = _(diagnose_dict[field])
                    except KeyError:
                        column = field
                        raise ParsingError(column)
                
                mod_num = Diagnose.Modalities.labels.index(mod)
                new_diagnosis = Diagnose(
                    patient=patient, modality=mod_num, side=side,
                    diagnose_date=diagnose_date,
                    **valid_diagnose_dict
                )
                new_diagnosis.save()
    

def import_from_pandas(
    data_frame: pd.DataFrame, 
    user,
    anonymize: List[str] = ["id"]
) -> Tuple[int]:
    """Batch-import patients from a ``pandas`` :class:`DataFrame` by iterating 
    through the rows and creating first the patient, their tumor(s) and then 
    their diagnose(s).
    
    Args:
        data_frame: The table containing rows of patients.
        user: The currently logged-in user. They will pass on their institution 
            to the new patients.
        anonymize: This will be passed on to :func:`row2patient`. It specifies 
            which fields are going to be used to compute the patient's hash and 
            thereby anonymize the patient.
    
    Returns:
        A tuple with the number of newly added patients and the number of 
        skipped rows, because they were already in the database.
    """
    num_new = 0
    num_skipped = 0
    
    for i, row in data_frame.iterrows():
        # Make sure first two levels are correct for patient data
        try:
            patient_row = row[("patient", "#")]
        except KeyError:
            missing = "('patient', '#', '...')"
            message = ("For patient info, first level must be 'patient', "
                       "second level must be '#'.")
            raise ParsingError(column=missing, message=message)
        
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
            missing = "('tumor', '1/2/3/...', '...')"
            message = ("For tumor info, first level must be 'tumor' and "
                       "second level must be number of tumor.")
            raise ParsingError(column=missing, message=message)
                
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
    

def export_to_pandas(patients: QuerySet) -> pd.DataFrame:
    """Export a QuerySet of patients to a pandas DataFrame of the same 
    structure as the one that is necessary to batch-import patients.
    
    Args:
        patients: A QuerySet of patients.
        
    Returns:
        The properly formatted table where each row corresponds to a patient.
    """
    
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
    for mod in Diagnose.Modalities.labels:
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
            mod = Diagnose.Modalities(diagnose.modality).label
            side = diagnose.side
            new_row[(mod, "info", "date")] = diagnose.diagnose_date
            for field in diagnose_fields:
                new_row[(mod, side, field)] = getattr(diagnose, field)
        
        df = df.append(new_row, ignore_index=True)
    
    return df
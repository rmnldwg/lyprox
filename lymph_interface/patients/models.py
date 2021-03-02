from django.db import models

from .utils import compute_hash
from .utils import nan_to_None as _

import pandas
import numpy as np
import dateutil.parser


T_STAGES = [
    (0, "T0"),
    (1, "T1"),
    (2, "T2"),
    (3, "T3"),
    (4, "T4")
]
N_STAGES = [
    (0, "N0"),
    (1, "N1"),
    (2, "N2"),
    (3, "N3")
]
M_STAGES = [
    (0, "M0"),
    (1, "M1"),
    (2, "MX")
]
class Patient(models.Model):
    """Base model class of a patient. Contains patient specific information."""
    identifier = models.CharField(max_length=200, unique=True) # ideally, this is a hashed id
    gender = models.CharField(max_length=10, choices=[("female", "female"), 
                                                      ("male"  , "male"  )])
    age = models.IntegerField()
    diagnose_date = models.DateField()
    
    alcohol_abuse = models.BooleanField(blank=True, null=True)
    nicotine_abuse = models.BooleanField(blank=True, null=True)
    hpv_status = models.BooleanField(blank=True, null=True) 
    
    t_stage = models.PositiveSmallIntegerField(choices=T_STAGES, default=0)
    n_stage = models.PositiveSmallIntegerField(choices=N_STAGES)
    m_stage = models.PositiveSmallIntegerField(choices=M_STAGES)
    
    
    def __str__(self):
        """Report some patient specifics."""
        return f"ID: {self.identifier}, age: {self.age}, gender: {self.gender}"
    
    
    
def create_from_pandas(data_frame, anonymize=True):
    """Create a batch of new patients from a pandas `DataFrame`."""
    num_new = len(data_frame)

    for i, row in data_frame.iterrows():
        # PATIENT
        # privacy-related fields that also serve identification purposes
        if anonymize:
            # first_name = row[("patient", "general", "first_name")]
            # last_name = row[("patient", "general", "last_name")]
            # birthday = row[("patient", "general", "birthday")]
            kisim_id = row[("patient", "general", "ID")]
            identifier = compute_hash(kisim_id)
        else:
            identifier = row[("patient", "general", "ID")]
            
        gender = _(row[("patient", "general", "gender")])
        age = _(row[("patient", "general", "age")])
        diagnose_date = dateutil.parser.parse(_(row[("patient", "general", "date")]))
        
        alcohol_abuse = _(row[("patient", "abuse", "alcohol")])
        nicotine_abuse = _(row[("patient", "abuse", "nicotine")])
        hpv_status = _(row[("patient", "condition", "HPV")])
        
        t_stage = 0
        n_stage = _(row[("patient", "stage", "N")])
        m_stage = _(row[("patient", "stage", "M")])
        
        new_patient = Patient(identifier=identifier, 
                              gender=gender, 
                              age=age, 
                              diagnose_date=diagnose_date, 
                              alcohol_abuse=alcohol_abuse, 
                              nicotine_abuse=nicotine_abuse, 
                              hpv_status=hpv_status,
                              t_stage=t_stage,
                              n_stage=n_stage,
                              m_stage=m_stage)
        new_patient.save()
        
        # TUMORS
        location_list = [tuple[1] for tuple in LOCATIONS]
        stages_list = [tuple[1] for tuple in T_STAGES]
        
        count = 1
        while ("tumor", f"{count}", "location") in data_frame.columns:
            location = _(location_list.index(row[("tumor", f"{count}", "location")]))
            position = _(row[("tumor", f"{count}", "side")])
            extension = _(row[("tumor", f"{count}", "extension")])
            size = _(row[("tumor", f"{count}", "size")])
            stage_prefix = _(row[("tumor", f"{count}", "prefix")])
            t_stage = _(row[("tumor", f"{count}", "stage")])
            
            new_tumor = Tumor(location=location,
                              position=position,
                              extension=extension,
                              size=size,
                              t_stage=t_stage,
                              stage_prefix=stage_prefix)
            new_tumor.patient = new_patient
            
            new_tumor.save()
            
            if new_tumor.t_stage > new_patient.t_stage:
                new_patient.t_stage = new_tumor.t_stage
                new_patient.save()
                
            count += 1
            
        # DIAGNOSES
        # first, find out which diagnoses are present in this DataFrame
        header_first_row = list(set([item[0] for item in data_frame.columns]))
        pat_index = header_first_row.index("patient")
        header_first_row.pop(pat_index)
        tum_index = header_first_row.index("tumor")
        header_first_row.pop(tum_index)
        
        for modality in header_first_row:
            modality_list = [item[1] for item in MODALITIES]
            modality_idx = modality_list.index(modality)
            
            # can be empty...
            try:
                diagnose_date = dateutil.parser.parse(_(row[(f"{modality}", "info", "date")]))
            except:
                diagnose_date = None
            
            if diagnose_date is not None:      
                for side in ["right", "left"]:
                    lnl_I = _(row[(f"{modality}", f"{side}", "I")])
                    lnl_II = _(row[(f"{modality}", f"{side}", "II")])
                    lnl_III = _(row[(f"{modality}", f"{side}", "III")])
                    lnl_IV = _(row[(f"{modality}", f"{side}", "IV")])
                    
                    new_diagnose = Diagnose(modality=modality_idx, 
                                            diagnose_date=diagnose_date,
                                            side=side,
                                            lnl_I=lnl_I,
                                            lnl_II=lnl_II,
                                            lnl_III=lnl_III,
                                            lnl_IV=lnl_IV)
                    
                    new_diagnose.patient = new_patient
                    new_diagnose.save()
        
    return num_new

    
    
LOCATIONS = [
    (0, "oral cavity"),
    (1, "oropharynx"),
    (2, "hypopharynx"),
    (3, "larynx")
]
class Tumor(models.Model):
    """Report of primary tumor(s)."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    
    location = models.PositiveSmallIntegerField(choices=LOCATIONS)
    position = models.CharField(max_length=10, choices=[("left", "left"),
                                                        ("right", "right"), 
                                                        ("central", "central")])
    extension = models.BooleanField(blank=True, null=True)
    size = models.FloatField(blank=True, null=True)
    
    t_stage = models.PositiveSmallIntegerField(choices=T_STAGES)
    stage_prefix = models.CharField(max_length=1, choices=[("c", "c"), 
                                                           ("p", "p")])
    
    

MODALITIES = [
    (0, "CT"),
    (1, "MRI"),
    (2, "PET"),
    (3, "FNA"),
    (4, "path"),
    (5, "pCT")
]
class Diagnose(models.Model):
    """Report of pattern of lymphatic metastases for a given diagnostic 
    modality."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    
    modality = models.PositiveSmallIntegerField(choices=MODALITIES)
    diagnose_date = models.DateField(blank=True, null=True)
    
    side = models.CharField(max_length=10, choices=[("left", "left"),
                                                    ("right", "right")])
    
    lnl_I   = models.BooleanField(blank=True, null=True)
    lnl_II  = models.BooleanField(blank=True, null=True)
    lnl_III = models.BooleanField(blank=True, null=True)
    lnl_IV  = models.BooleanField(blank=True, null=True)

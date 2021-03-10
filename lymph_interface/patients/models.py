from django.db import models

from .utils import compute_hash, create_from_pandas
from .utils import nan_to_None as _

import pandas
import numpy as np
import dateutil.parser


T_STAGES = [
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

from django.db import models

import pandas
import numpy as np
import dateutil.parser


# TNM staging system
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
    (3, "N3"),
]
M_STAGES = [
    (0, "M0"),
    (1, "M1"),
    (2, "MX")
]
class Patient(models.Model):
    """Base model class of a patient. Contains patient specific information."""
    # this first field should be computed from the fields that must be deleted 
    # for anomymization.
    hash_value = models.CharField(max_length=200, unique=True)
    gender = models.CharField(max_length=10, choices=[("female", "female"), 
                                                      ("male"  , "male"  )])
    age = models.IntegerField()
    diagnose_date = models.DateField()
    
    alcohol_abuse = models.BooleanField(blank=True, null=True)
    nicotine_abuse = models.BooleanField(blank=True, null=True)
    hpv_status = models.BooleanField(blank=True, null=True) 
    neck_dissection = models.BooleanField(blank=True, null=True)
    
    t_stage = models.PositiveSmallIntegerField(choices=T_STAGES, default=0)
    n_stage = models.PositiveSmallIntegerField(choices=N_STAGES)
    m_stage = models.PositiveSmallIntegerField(choices=M_STAGES)
    
    
    def __str__(self):
        """Report some patient specifics."""
        return f"pk {self.pk} | {self.age} yo | {self.gender}"



# some locations where the primary tumor can occur
LOCATIONS = [
    (0, "oral cavity"),
    (1, "oropharynx"),
    (2, "hypopharynx"),
    (3, "larynx")
]
# finer classification of the location, along with the corresponding ICD code
SUBSITES = [
    ("oral cavity", (("C03.0", "upper gum"),
                     ("C03.1", "lower gum"),
                     ("C03.9", "gum, nos"),

                     ("C04.0", "anterior floor of mouth"),
                     ("C04.1", "lateral floor of mouth"),
                     ("C04.8", "overlapping lesion of floor of mouth"),
                     ("C04.9", "floor of mouth, nos"),

                     ("C05.0", "hard palate"),
                     ("C05.1", "soft palate, nos"),
                     ("C05.2", "uvula"),
                     ("C05.8", "overlapping lesion of palate"),
                     ("C05.9", "palate, nos"),

                     ("C06.0", "cheeck mucosa"),
                     ("C06.1", "vestibule of mouth"),
                     ("C06.2", "retromolar area"),
                     ("C06.8", "overlapping lesion(s) of NOS parts of mouth"),
                     ("C06.9", "mouth, nos"),)
     ),
    ("oropharynx",  (("C01.9", "base of tongue, nos"),

                     ("C09.0", "tonsillar fossa"),
                     ("C09.1", "tonsillar pillar"),
                     ("C09.8", "overlapping lesion of tonsil"),
                     ("C09.9", "tonsil, nos"),

                     ("C10.0", "vallecula"),
                     ("C10.1", "anterior surface of epiglottis"),
                     ("C10.2", "lateral wall of oropharynx"),
                     ("C10.3", "posterior wall of oropharynx"),
                     ("C10.4", "branchial cleft"),
                     ("C10.8", "overlapping lesions of oropharynx"),
                     ("C10.9", "oropharynx, nos"),)
     ),
    ("hypopharynx", (("C12.9", "pyriform sinus"),

                     ("C13.0", "postcricoid region"),
                     ("C13.1", "hypopharyngeal aspect of aryepiglottic fold"),
                     ("C13.2", "posterior wall of hypopharynx"),
                     ("C13.8", "overlapping lesion of hypopharynx"),
                     ("C13.9", "hypopharynx, nos"),)
     ),
    ("larynx",      (("C32.0", "glottis"),
                     ("C32.1", "supraglottis"),
                     ("C32.2", "subglottis"),
                     ("C32.3", "laryngeal cartilage"),
                     ("C32.8", "overlapping lesion of larynx"),
                     ("C32.9", "larynx, nos"),)
     )
]
class Tumor(models.Model):
    """Report of primary tumor(s)."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    
    location = models.PositiveSmallIntegerField(choices=LOCATIONS, null=True)
    subsite = models.CharField(max_length=10, choices=SUBSITES)
    position = models.CharField(max_length=10, choices=[("left", "left"),
                                                        ("right", "right"), 
                                                        ("central", "central")])
    extension = models.BooleanField(blank=True, null=True)
    size = models.FloatField(blank=True, null=True)
    
    t_stage = models.PositiveSmallIntegerField(choices=T_STAGES)
    stage_prefix = models.CharField(max_length=1, choices=[("c", "c"), 
                                                           ("p", "p")])
    
    
    def __str__(self):
        """Report some main characteristics."""
        return f"pk {self.pk} | belongs to {self.patient.pk} | subsite {self.subsite} | T{self.t_stage}"
    
    

# diagnostic modalities that are used to detect metastases in LNLs
MODALITIES = [
    (0, "CT"),
    (1, "MRI"),
    (2, "PET"),
    (3, "FNA"),
    (4, "path"),
    (5, "pCT")
]
# Lymph node levels in the head & neck region
LNLs = [
    "I", "Ia" , "Ib",
    "II", "IIa", "IIb",
    "III",
    "IV",
    "V",
    "VII"
]
class Diagnose(models.Model):
    """Report of pattern of lymphatic metastases for a given diagnostic 
    modality."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    
    modality = models.PositiveSmallIntegerField(choices=MODALITIES)
    diagnose_date = models.DateField(blank=True, null=True)
    
    side = models.CharField(max_length=10, choices=[("left", "left"),
                                                    ("right", "right")])
    
    
    def __str__(self):
        """Report some info for admin view."""
        return f"pk {self.pk} | belongs to {self.patient.pk} | {self.get_modality_display()} | {self.side} side"
    
    
# add lymph node level fields to model 'Diagnose'
for lnl in LNLs:
    Diagnose.add_to_class(lnl, models.BooleanField(blank=True, null=True))

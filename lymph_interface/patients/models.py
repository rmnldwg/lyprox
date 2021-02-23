from django.db import models

# Create your models here.
class Patient(models.Model):
    """Base model class of a patient. Contains patient specific information."""
    identifier = models.CharField(max_length=200) # ideally, this is a hashed id
    gender = models.CharField(max_length=10, choices=[("female", "female"), 
                                                      ("male"  , "male"  )])
    age = models.IntegerField()
    
    alcohol_abuse = models.BooleanField()
    nicotine_abuse = models.BooleanField()
    hpv_status = models.BooleanField() 
    
    
    def __str__(self):
        """Report some patient specifics."""
        return f"ID: {self.identifier}, age: {self.age}, gender: {self.gender}"
    


TREATMENT_KIND = [
    (0, "radiotherapy"),
    (1, "chemotherapy"),
    (2, "surgery"),
    (3, "immunotherapy")
]
class Treatment(models.Model):
    """Specifies the therapy a patient has received."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    
    kind = models.PositiveSmallIntegerField(choices=TREATMENT_KIND)
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    
    
LOCATIONS = [
    (0, "oral cavity"),
    (1, "oropharynx"),
    (2, "hypopharynx"),
    (3, "larynx")
]
T_STAGES = [
    (0, "T0"),
    (1, "T1"),
    (2, "T2"),
    (3, "T3"),
    (4, "T4")
]
class Tumor(models.Model):
    """Report of primary tumor(s)."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    
    diagnose_date = models.DateField()
    
    location = models.PositiveSmallIntegerField(choices=LOCATIONS)
    t_stage = models.PositiveSmallIntegerField(choices=T_STAGES)
    stage_prefix = models.CharField(max_length=1, choices=[("c", "c"), 
                                                           ("p", "p")])
    
    
N_STAGES = [
    (0, "N0"),
    (1, "N1"),
    (2, "N2"),
    (3, "N3")
]
M_STAGES = [
    (0, "M0"),
    (1, "M1")
]
MODALITIES = [
    (0, "CT"),
    (1, "MRI"),
    (2, "PET"),
    (3, "FNA"),
    (4, "neck dissection")
]
class Diagnose(models.Model):
    """Report of pattern of lymphatic metastases for a given diagnostic 
    modality."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    
    diagnose_date = models.DateField()
    
    modality = models.PositiveSmallIntegerField(choices=MODALITIES)
    
    n_stage = models.PositiveSmallIntegerField(choices=N_STAGES)
    m_stage = models.PositiveSmallIntegerField(choices=M_STAGES)
    
    lnl_I   = models.BooleanField(blank=True, null=True, default=None)
    lnl_II  = models.BooleanField(blank=True, null=True, default=None)
    lnl_III = models.BooleanField(blank=True, null=True, default=None)
    lnl_IV  = models.BooleanField(blank=True, null=True, default=None)
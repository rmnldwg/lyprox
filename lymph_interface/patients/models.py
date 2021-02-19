from django.db import models

# Create your models here.
class Patient(models.Model):
    """Base model class of a patient. Contains patient specific information."""
    identifier = models.CharField(max_length=200) # ideally, this is a hashed id
    gender = models.CharField(max_length=6, choices=["male". "female"])
    age = models.IntegerField()
    
    diagnose_date = models.DateField()
    stage_prefix = models.CharField(max_length=1, choices=["c", "p"])
    t_stage = models.CharField(max_length=3, choices=["Tx", "Tis", "T0", 
                                                      "T1", "T2", "T3", "T4"])
    n_stage = models.CharField(max_length=2, choices=["Nx", "N0", 
                                                      "N1", "N2", "N3", "N4"])
    m_stage = models.CharField(max_length=2, choices=["M0", "M1"])
    
    alcohol_abuse = models.BooleanField()
    nicotine_abuse = models.BooleanField()
    hpv_status - models.BooleanField() 
    
    
class Therapy(models.Model):
    """Specifies the therapy a patient has received."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    
    treatment_type = models.CharField(max_length=20, choices=["radiotherapy", 
                                                              "chemotherapy", 
                                                              "surgery", 
                                                              "immunotherapy"])
    start_date = models.DateField()
    end_date = models.DateField()
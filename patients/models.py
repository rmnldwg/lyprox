from django.db import models
from django.urls import reverse

import pandas
import numpy as np

from .loggers import ModeLoggerMixin


class Patient(ModeLoggerMixin, models.Model):
    """Base model class of a patient. Contains patient specific information."""
    
    class T_stages(models.IntegerChoices):
        T1 = 1, "T1"
        T2 = 2, "T2"
        T3 = 3, "T3"
        T4 = 4, "T4"
    
    class N_stages(models.IntegerChoices):
        N0 = 0, "N0"
        N1 = 1, "N1"
        N2 = 2, "N2"
        N3 = 3, "N3"
        
    class M_stages(models.IntegerChoices):
        M0 = 0, "M0"
        M1 = 1, "M1"
        MX = 2, "MX"
    
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
    
    t_stage = models.PositiveSmallIntegerField(choices=T_stages.choices, default=0)
    n_stage = models.PositiveSmallIntegerField(choices=N_stages.choices)
    m_stage = models.PositiveSmallIntegerField(choices=M_stages.choices)
    
    
    def __str__(self):
        """Report some patient specifics."""
        return f"pk {self.pk} | {self.age} yo | {self.gender}"
    
    def get_absolute_url(self):
        return reverse("patients:detail", args=[self.pk])
    
    def update_t_stage(self):
        """Update T-stage after new `Tumor` is added to `Patient` (gets called 
        in `Tumor.save()` method)"""
        tumors = Tumor.objects.all().filter(patient=self)
        
        max_t_stage = 0
        for tumor in tumors:
            if max_t_stage < tumor.t_stage:
                max_t_stage = tumor.t_stage
                
        self.t_stage = max_t_stage
        self.save()
        self.logger.debug(f"T-stage of patient {self} updated to "
                          f"{self.get_t_stage_display()}.")


class Tumor(ModeLoggerMixin, models.Model):
    """Report of primary tumor(s)."""
    
    class Locations(models.IntegerChoices):
        ORAL_CAVITY = 0, "oral cavity"
        OROPHARYNX  = 1, "oropharynx"
        HYPOPHARYNX = 2, "hypopharynx"
        LARYNX      = 3, "larynx"
        
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
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    
    location = models.PositiveSmallIntegerField(choices=Locations.choices, null=True)
    subsite = models.CharField(max_length=10, choices=SUBSITES)
    side = models.CharField(max_length=10, choices=[("left", "left"),
                                                    ("right", "right"),
                                                    ("central", "central")])
    extension = models.BooleanField(blank=True, null=True)
    volume = models.FloatField(blank=True, null=True)
    
    t_stage = models.PositiveSmallIntegerField(choices=Patient.T_stages.choices)
    stage_prefix = models.CharField(max_length=1, choices=[("c", "c"), 
                                                           ("p", "p")])
    
    def __str__(self):
        """Report some main characteristics."""
        return f"pk {self.pk} | belongs to {self.patient.pk} | subsite {self.subsite} | T{self.t_stage}"
    
    def save(self, *args, **kwargs):
        """Extract location and update patient's T-stage upon saving tumor."""
        # automatically extract location from subsite
        subsite_dict = dict(self.SUBSITES)
        location_list = self.Locations.labels
        
        found_location = False
        for i, loc in enumerate(location_list):
            loc_subsites = [tpl[1] for tpl in subsite_dict[loc]]
            if self.get_subsite_display() in loc_subsites:
                self.location = i
                found_location = True
                
        if not found_location:
            self.logger.warn("Could not extract location for this tumor's "
                             f"({self}) subsite ({self.get_subsite_display()})")
                    
        tmp_return = super(Tumor, self).save(*args, **kwargs)
    
        # call patient's `update_t_stage` method
        self.patient.update_t_stage()
        
        return tmp_return
        
    def delete(self, *args, **kwargs):
        patient = self.patient
        tmp = super(Tumor, self).delete(*args, **kwargs)
        patient.update_t_stage()
        return tmp
    

class Diagnose(models.Model):
    """Report of pattern of lymphatic metastases for a given diagnostic 
    modality."""
    
    LNLs = [
        "I", "Ia" , "Ib", "II", "IIa", "IIb", "III", "IV", "V", "VII"
    ]
    
    class Modalities(models.IntegerChoices):
        CT   = 0, "CT"
        MRI  = 1, "MRI"
        PET  = 2, "PET"
        FNA  = 3, "FNA"
        PATH = 4, "path"
        PCT  = 5, "pCT"
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    
    modality = models.PositiveSmallIntegerField(choices=Modalities.choices)
    diagnose_date = models.DateField(blank=True, null=True)
    
    side = models.CharField(max_length=10, choices=[("left", "left"),
                                                    ("right", "right")])
    
    def __str__(self):
        """Report some info for admin view."""
        return f"pk {self.pk} | belongs to {self.patient.pk} | {self.get_modality_display()} | {self.side} side"
    
    
# add lymph node level fields to model 'Diagnose'
for lnl in Diagnose.LNLs:
    Diagnose.add_to_class(lnl, models.BooleanField(blank=True, null=True))

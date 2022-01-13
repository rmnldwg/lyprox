from accounts.models import Institution
from django.db import models
from django.urls import reverse
from dateutil.parser import ParserError, parse

from core.loggers import ModelLoggerMixin


class RobustDateField(models.DateField):
    """DateField that doesn't raise a ValidationError when the date string isn't 
    formated according to ISO (YYYY-MM-DD)
    """
    def to_python(self, value):
        if type(value) == str:
            try:
                value = parse(value).date()
            except ParserError:
                return None
                
        return super().to_python(value)


class Patient(ModelLoggerMixin, models.Model):
    """The representation of a patient in the database. It contains some 
    demographic information, as well as patient-specific characteristics that 
    are important in the context of cancer, e.g. HPV status."""
    
    class T_stages(models.IntegerChoices):
        """:meta private:"""
        T1 = 1, "T1"
        T2 = 2, "T2"
        T3 = 3, "T3"
        T4 = 4, "T4"
    
    class N_stages(models.IntegerChoices):
        """:meta private:"""
        N0 = 0, "N0"
        N1 = 1, "N1"
        N2 = 2, "N2"
        N3 = 3, "N3"
        
    class M_stages(models.IntegerChoices):
        """:meta private:"""
        M0 = 0, "M0"
        M1 = 1, "M1"
        MX = 2, "MX"
    
    #: Unique ID that should be computed from sensitive info upon patient 
    #: creation to avoid duplicates and respect the patient's privacy.
    hash_value = models.CharField(max_length=200, unique=True)
    sex = models.CharField(max_length=10, choices=[("female", "female"),
                                                   ("male"  , "male"  )])  #:
    age = models.IntegerField()  #:
    diagnose_date = RobustDateField()  #:
    
    #: Was the patient a drinker?
    alcohol_abuse = models.BooleanField(blank=True, null=True)
    #: Was the patient a smoker?
    nicotine_abuse = models.BooleanField(blank=True, null=True)
    #: HPV status of the patient (postive or negative).
    hpv_status = models.BooleanField(blank=True, null=True) 
    #: Has the patient been treated with some form of neck dissection?
    neck_dissection = models.BooleanField(blank=True, null=True)
    
    tnm_edition = models.PositiveSmallIntegerField(default=8)  #:
    stage_prefix = models.CharField(
        max_length=1, choices=[("c", "c"), ("p", "p")], default='c'
    )  #:
    t_stage = models.PositiveSmallIntegerField(
        choices=T_stages.choices, default=0
    )  #:
    n_stage = models.PositiveSmallIntegerField(choices=N_stages.choices)  #:
    m_stage = models.PositiveSmallIntegerField(choices=M_stages.choices)  #:
    
    #: By default, every newly created patient is assigned to the institution 
    #: of the :class:`User` that created them.
    institution = models.ForeignKey(
        Institution, blank=True, on_delete=models.PROTECT
    )
    
    def __str__(self):
        """Report some patient specifics."""
        return (f"#{self.pk}: {self.sex} ({self.age}) at "
                f"{self.institution.shortname}")
    
    def get_absolute_url(self):
        """Return the absolute URL for a particular patient."""
        return reverse("patients:detail", args=[self.pk])
    
    def get_tumors(self):
        tumors = Tumor.objects.all().filter(patient=self)
        return tumors
    
    def get_diagnoses(self):
        diagnoses = Diagnose.objects.all().filter(patient=self)
        return diagnoses
    
    def update_t_stage(self):
        """Update T-stage after new :class:`Tumor` is added to :class:`Patient` 
        (gets called in :meth:`Tumor.save()` method). Also updates the patient's 
        stage prefix to that of the tumor with the highest T-category.
        """
        tumors = Tumor.objects.all().filter(patient=self)
        
        max_t_stage = 0
        stage_prefix = 'c'
        for tumor in tumors:
            if max_t_stage < tumor.t_stage:
                max_t_stage = tumor.t_stage
                stage_prefix = tumor.stage_prefix
                
        self.t_stage = max_t_stage
        self.stage_prefix = stage_prefix
        self.save()
        self.logger.debug(f"T-stage of patient {self} updated to "
                          f"{self.get_stage_prefix_display()}"
                          f"{self.get_t_stage_display()}.")


class Tumor(ModelLoggerMixin, models.Model):
    """Model to describe tumors in detail. It is connected to a patient via 
    a ``ForeignKey`` relation."""
    
    class Locations(models.TextChoices):
        """:meta private:"""
        ORAL_CAVITY = "oral cavity"
        OROPHARYNX  = "oropharynx"
        HYPOPHARYNX = "hypopharynx"
        LARYNX      = "larynx"
        
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
    
    SUBSITE_DICT = {"base":        ["C01.9"], 
                    "tonsil":      ["C09.0", "C09.1", "C09.8", "C09.9"],
                    "rest_oro":    ["C10.0", "C10.1", "C10.2", "C10.3", 
                                    "C10.4","C10.8", "C10.9"],
                    "rest_hypo":   ["C12.9", "C13.0", "C13.1", "C13.2", 
                                    "C13.8", "C13.9"],
                    "glottis":     ["C32.0"],
                    "rest_larynx": ["C32.1", "C32.2", "C32.3", "C32.8", "C32.9"]}
    
    #: ``ForeignKey`` to :class:`Patient`
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    
    #: Tumor location within the Head & Neck region
    location = models.CharField(max_length=20, choices=Locations.choices)
    #: More detailed information about the location of the tumor
    subsite = models.CharField(max_length=10, choices=SUBSITES)
    #: Lateralization of the tumor.
    side = models.CharField(max_length=10, choices=[("left", "left"),
                                                    ("right", "right"),
                                                    ("central", "central")])
    #: Does the tumor extend over the mid-sagittal plane?
    extension = models.BooleanField(blank=True, null=True)
    #: Size of the tumor.
    volume = models.FloatField(blank=True, null=True)
    
    #:
    t_stage = models.PositiveSmallIntegerField(choices=Patient.T_stages.choices)
    #: Prefix for the tumor's T-stage (``c`` or ``p``)
    stage_prefix = models.CharField(max_length=1, choices=[("c", "c"), 
                                                           ("p", "p")])
    
    def __str__(self):
        """Report some main characteristics."""
        return f"#{self.pk}: T{self.t_stage} tumor of patient #{self.patient.pk}"
    
    def save(self, *args, **kwargs):
        """Before creating the database entry, determine the location of the 
        tumor from the specified subsite and update the patient it is assigned 
        to, to the correct T-stage."""
        
        # Automatically extract location from subsite
        subsite_dict = dict(self.SUBSITES)
        location_list = self.Locations.values
        
        found_location = False
        for loc in location_list:
            loc_subsites = [tpl[1] for tpl in subsite_dict[loc]]
            if self.get_subsite_display() in loc_subsites:
                self.location = loc
                found_location = True
                
        if not found_location:
            self.logger.warn("Could not extract location for this tumor's "
                             f"({self}) subsite ({self.get_subsite_display()})")
                    
        tmp_return = super(Tumor, self).save(*args, **kwargs)
    
        # call patient's `update_t_stage` method
        self.patient.update_t_stage()
        
        return tmp_return
        
    def delete(self, *args, **kwargs):
        """Upon deletion, update the patient's T-stage."""
        patient = self.patient
        tmp = super(Tumor, self).delete(*args, **kwargs)
        patient.update_t_stage()
        return tmp
    

class Diagnose(ModelLoggerMixin, models.Model):
    """Model describing the diagnosis of one side of a patient's neck with 
    regard to their lymphaitc metastatic involvement."""
    
    LNLs = [
        "I", "Ia" , "Ib", "II", "IIa", "IIb", "III", "IV", "V", "VII"
    ]
    
    class Modalities(models.IntegerChoices):
        """:meta private:"""
        CT   = 0, "CT"
        MRI  = 1, "MRI"
        PET  = 2, "PET"
        FNA  = 3, "FNA"
        PATH = 4, "path"
        PCT  = 5, "pCT"
    
    #: ``ForeignKey`` to :class:`Patient`
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    
    #: The used diagnostic modality. E.g. ``MRI``, ``PET`` or ``FNA``.
    modality = models.PositiveSmallIntegerField(choices=Modalities.choices)
    #:
    diagnose_date = RobustDateField(blank=True, null=True)
    #: diagnosed side
    side = models.CharField(max_length=10, choices=[("left", "left"),
                                                    ("right", "right")])
    
    def __str__(self):
        """Report some info for admin view."""
        return (f"#{self.pk}: {self.get_modality_display()} diagnose "
                f"({self.side}) of patient #{self.patient.pk}")
    
    def save(self, *args, **kwargs):
        """Make sure LNLs and their sublevels (e.g. 'a' and 'b') are treated 
        consistelntly. E.g. when sublevel ``Ia`` is reported to be involved, 
        the involvement status of level ``I`` cannot be reported as healthy.
        """
        safe_negate = lambda x: False if x is None else not x
        
        # LNL I (a and b)
        if any([self.Ia, self.Ib]):
            self.I = True
        elif all([safe_negate(self.Ia), safe_negate(self.Ib)]):
            self.I = False


        # LNL II (a and b)
        if any([self.IIa, self.IIb]):
            self.II = True
        elif all([safe_negate(self.IIa), safe_negate(self.IIb)]):
            self.II = False

        
        return super().save(*args, **kwargs)
    
    
# add lymph node level fields to model 'Diagnose'
for lnl in Diagnose.LNLs:
    Diagnose.add_to_class(lnl, models.BooleanField(blank=True, null=True))

"""
This module defines how patient related models are defined and how they
interact with each other. Currently, three models are implemented: The
`Patient`, `Tumor` and the `Diagnose`. Each `Patient` can have multiple `Tumor`
and `Diagnose` entries associated with it, which is defined by the
``django.db.models.ForeignKey`` attribute in the `Tumor` and `Diagnose` class.

There are also custom methods implemented, making sure that e.g. the diagnosis
of a sublevel (lets say ``Ia``) is consistent with the diagnosis of the
respective superlevel (in that case ``I``).

In addition, the module defines a `Dataset` model that enables users to
download CSV tables with patient of a particular institution's cohort.
"""
# pylint: disable=no-member
# pylint: disable=logging-fstring-interpolation

import os
from io import StringIO
from collections import namedtuple
import pandas as pd
import hashlib

from dateutil.parser import ParserError, parse
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.core.files.base import ContentFile
from django.core.exceptions import EmptyResultSet, ValidationError
from django.conf import settings

from accounts.models import Institution
from core.loggers import ModelLoggerMixin
import patients.ioports as io


class RobustDateField(models.DateField):
    """
    DateField that doesn't raise a ValidationError when the date string isn't
    formated according to ISO (YYYY-MM-DD)
    """
    def to_python(self, value):
        if isinstance(value, str):
            try:
                value = parse(value).date()
            except ParserError:
                return None

        return super().to_python(value)


class DatasetIsLocked(Exception):
    """Indicates that a locked dataset cannot be changed."""
    pass

def compute_md5_hash(file):
    """Compute md5 hash of file."""
    file.open("rb")
    md5_hash = hashlib.md5(file.read())
    file.close()
    return md5_hash

def _get_filepath(instance, filename, folder, file=None) -> str:
    """Compile the filepath for storing the CSV file."""
    full_dirpath = os.path.join(settings.MEDIA_ROOT, folder)
    os.makedirs(full_dirpath, exist_ok=True)

    if file is not None:
        filename = compute_md5_hash(file).hexdigest()

    rel_filepath = f"{folder}/{filename}.csv"
    return rel_filepath

def get_upload_filepath(instance, filename) -> str:
    """Compile the filepath for storing the uploaded CSV file."""
    return _get_filepath(
        instance, filename, folder="upload_csv", file=instance.upload_csv
    )

def get_export_filepath(instance, filename) -> str:
    """Compile the filepath for storing the exported CSV file."""
    return _get_filepath(
        instance, filename, folder="export_csv", file=instance.export_csv
    )


class Dataset(ModelLoggerMixin, models.Model):
    """
    Model that represents a dataset as it was provided by the source. This
    means e.g. that it captures the raw data in CSV format along with some
    important metadata. It also serves as an interface between CSV and the SQL
    database.
    """
    name = models.CharField(max_length=128)
    """Name of the dataset."""
    description = models.TextField()
    """A brief description of the dataset."""
    create_date = models.DateField(default=timezone.now)
    """Date when the dataset was uploaded."""
    upload_csv = models.FileField(
        upload_to=get_upload_filepath,
        validators=[FileExtensionValidator(allowed_extensions=["csv"])],
        null=True, blank=True,
    )
    """CSV file that is uploaded via the form. Can be null in the database to
    allow creating a dataset by manually creating patients one by one."""
    export_csv = models.FileField(
        validators=[FileExtensionValidator(allowed_extensions=["csv"])],
        null=True, blank=True,
    )
    """CSV file exported from the database. This file cannot be used to
    (re-)populate the database. It serves only the purpose to export manually
    created datasets in CSV form."""
    is_public = models.BooleanField(default=False)
    """Indicates if the dataset can be accessed by unauthenticated users."""
    is_locked = models.BooleanField(default=False)
    """Prevents editing the dataset or patients associated with it."""

    repo_provider = models.CharField(
        verbose_name="Repository Provider",
        max_length=128,
        blank=True, null=True
    )
    """Name of the repository provider, e.g. GitHub (optional)."""
    repo_url = models.URLField(
        verbose_name="Link to Repository",
        blank=True, null=True
    )
    """URL to the repository, e.g. a DOI identifier (optional)."""

    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE
    )
    """The institution that provided the dataset."""

    def __str__(self):
        year = self.create_date.strftime("%Y")
        inst_short = self.institution.shortname
        return f"{year}-{inst_short}-{self.name}"

    def lock(self):
        """Lock the dataset to prevent editing it or its patients."""
        self.is_locked = True
        self.save(override=True)

    def unlock(self):
        """Unlock the dataset to allow editing again."""
        self.is_locked = False
        self.save()

    def validate_unique(self, *args, **kwargs) -> None:
        """Make sure the same file cannot be uploaded twice."""
        super().validate_unique(*args, **kwargs)
        upload_filename = compute_md5_hash(self.upload_csv).hexdigest() + ".csv"
        filepath = os.path.join(
            settings.MEDIA_ROOT, "upload_csv", upload_filename
        )
        if os.path.exists(filepath):
            raise ValidationError(
                {"upload_csv": "File has already been uploaded"}
            )

    def save(self, *args, override=False, **kwargs):
        """Assign the MD5 hash of the data to the `md5_hash` field and load the
        CSV table into ."""
        if self.is_locked and not override:
            msg = "Cannot edit locked dataset."
            self.logger.error(msg)
            raise DatasetIsLocked(msg)

        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delete the files associated with the database as well."""
        self.upload_csv.delete(save=False)
        self.export_csv.delete(save=False)
        return super().delete(*args, **kwargs)

    def to_db(self):
        """
        Import data from an uploaded CSV file into database.
        """
        if self.upload_csv is None:
            self.logger.warning(
                "Only uploaded CSVs can be imported into database. Aborting"
            )
            return
            
        with self.upload_csv.open('r') as csv_file:
            table = pd.read_csv(csv_file, header=[0,1,2])

        if Patient.objects.all().filter(dataset=self).count() > 0:
            self.logger.warning(
                "There are already patients in the database. Aborting."
            )
            return

        n_new, n_skip = io.import_from_pandas(table=table, dataset=self)
        self.logger.info(
            f"{n_new} patients from dataset {self} added to database, "
            f"{n_skip} entries skipped"
        )

    def to_pandas(self) -> pd.DataFrame:
        """
        Export `Patient` objects belonging to this `Dataset` from the Django
        database to a `pandas.DataFrame`.
        """
        patients = Patient.objects.all().filter(dataset=self)
        if patients.count() == 0:
            msg = "Uploaded CSV has not been imported into database yet."
            self.logger.error(msg)
            raise EmptyResultSet(msg)

        return io.export_to_pandas(patients)

    def to_csv(self):
        """
        Export `Patient` objects belonging to this `Dataset` from the Django
        database first to a `pandas.DataFrame` and then save that as CSV file.
        Note: It does not save the dataset instance. That needs to be done
        separately afterwards.
        """
        patients_table = self.to_pandas()
        with StringIO() as buffer:
            patients_table.to_csv(buffer, index=None)
            csv_file = ContentFile(buffer.getvalue().encode("utf-8"))

        if self.export_csv is not None:
            self.export_csv.delete(save=False)

        file_hash = compute_md5_hash(csv_file).hexdigest()
        self.export_csv.save(f"export_csv/{file_hash}.csv", csv_file, save=True)


class Patient(ModelLoggerMixin, models.Model):
    """
    The representation of a patient in the database. It contains some
    demographic information, as well as patient-specific characteristics that
    are important in the context of cancer, e.g. HPV status.

    This model also ties together the information about the patient's tumor(s)
    and the lymphatic progression pattern of that patient in the form of a
    `Diagnose` model.
    """
    hash_value = models.CharField(max_length=200, unique=True)
    """Unique ID computed from sensitive info upon patient creation."""

    sex = models.CharField(max_length=10, choices=[("female", "female"),
                                                   ("male"  , "male"  )])
    age = models.IntegerField()
    diagnose_date = RobustDateField()
    """Date of histological confirmation with a squamous cell carcinoma."""

    alcohol_abuse = models.BooleanField(blank=True, null=True)
    """Was the patient a drinker?"""

    nicotine_abuse = models.BooleanField(blank=True, null=True)
    """Was the patient a smoker"""

    hpv_status = models.BooleanField(blank=True, null=True)
    """Was the patient HPV positive (``True``) or negative (``False``)?"""

    neck_dissection = models.BooleanField(blank=True, null=True)
    """Did the patient undergo (radical) neck dissection?"""

    tnm_edition = models.PositiveSmallIntegerField(default=8)
    """The edition of the TNM staging system that was used."""

    stage_prefix = models.CharField(
        max_length=1, choices=[("c", "c"), ("p", "p")], default='c'
    )
    """T-stage prefix: 'c' for 'clinical' and 'p' for 'pathological'."""

    class T_stages(models.IntegerChoices):
        """Defines the possible T-stages as choice class."""
        T1 = 1, "T1"
        T2 = 2, "T2"
        T3 = 3, "T3"
        T4 = 4, "T4"

    t_stage = models.PositiveSmallIntegerField(
        choices=T_stages.choices, default=0
    )
    """Stage of the primary tumor. Categorized the tumor by size and
    infiltration of tissue types."""

    class N_stages(models.IntegerChoices):
        """Defines the possible N-stages as choice class."""
        N0 = 0, "N0"
        N1 = 1, "N1"
        N2 = 2, "N2"
        N3 = 3, "N3"

    n_stage = models.PositiveSmallIntegerField(choices=N_stages.choices)
    """Categorizes the extend of regional metastases."""

    class M_stages(models.IntegerChoices):
        """Defines the possible M-stages as choice class."""
        M0 = 0, "M0"
        M1 = 1, "M1"
        MX = 2, "MX"

    m_stage = models.PositiveSmallIntegerField(choices=M_stages.choices)
    """Indicates whether or not there are distant metastases."""

    dataset = models.ForeignKey(
        Dataset, on_delete=models.CASCADE
    )
    """A newly created patient should be assigned to a dataset."""

    def __str__(self):
        """Report some patient specifics."""
        return (
            f"#{self.pk}: {self.sex} ({self.age}) from "
            f"{self.dataset.name}"
        )

    def get_absolute_url(self):
        """Return the absolute URL for a particular patient."""
        return reverse("patients:detail", args=[self.pk])

    def get_tumors(self):
        """Return the primary tumor(s) of that patient."""
        tumors = Tumor.objects.all().filter(patient=self)
        return tumors

    def get_diagnoses(self):
        """Return the LNL diagnose(s) of the patient."""
        diagnoses = Diagnose.objects.all().filter(patient=self)
        return diagnoses

    def update_t_stage(self):
        """
        Update T-stage after new `Tumor` is added to `Patient`
        (gets called in `Tumor.save` method). Also updates the patient's
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
        self.logger.debug(
            f"T-stage of patient {self} updated to "
            f"{self.get_stage_prefix_display()}{self.get_t_stage_display()}."
        )

    def save(self, *args, **kwargs):
        """Make sure patient is not added to locked dataset."""
        if self.dataset.is_locked:
            raise DatasetIsLocked("Cannot add patient to locked dataset.")

        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Block deletion if dataset is locked."""
        if self.dataset.is_locked:
            msg = "Cannot delete patient if dataset is locked."
            self.logger.error(msg)
            raise DatasetIsLocked(msg)
        
        return super().delete(*args, **kwargs)


class Tumor(ModelLoggerMixin, models.Model):
    """
    Model to describe a patient's tumor in detail. It is connected to a patient
    via a ``django.db.models.ForeignKey`` relation.
    """

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    """This defines the connection to the `Patient` model."""

    class Locations(models.TextChoices):
        """The primary tumor locations in the head and neck region."""
        ORAL_CAVITY = "oral cavity"
        OROPHARYNX  = "oropharynx"
        HYPOPHARYNX = "hypopharynx"
        LARYNX      = "larynx"

    location = models.CharField(max_length=20, choices=Locations.choices)
    """The tumor location."""

    SUBSITES = [
        ("oral cavity", (("C02.0", "dorsal surface of tongue"),
                         ("C02.1", "border of tongue"),
                         ("C02.2", "ventral surface of tongue"),
                         ("C02.3", "anterior two thirds of tongue"),
                         ("C02.4", "lingual tonsil"),
                         ("C02.8", "overlapping sites of tongue"),
                         ("C02.9", "tongue, nos"),

                         ("C03.0", "upper gum"),
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
                         ("C06.9", "mouth, nos"),

                         ("C08.0", "submandibular gland"),
                         ("C08.1", "sublingual gland"),
                         ("C08.9", "salivary gland, nos"))
        ),
        ("oropharynx",  (("C01"  , "base of tongue, nos"),

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
        ("hypopharynx", (("C12"  , "pyriform sinus"),

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
    """List of subsites with their ICD-10 code and respective description,
    grouped by location."""

    # NOTE: The ICD-10 codes `C01` and `C01.9` refer to the same subsite. `C01`
    # is correct, but for resilience, I also accept `C01.9` until I implement
    # my own ICD interface.
    SUBSITE_DICT = {
        "base":        ["C01"  , "C01.9"],
        "tonsil":      ["C09.0", "C09.1", "C09.8", "C09.9"],
        "rest_oro":    ["C10.0", "C10.1", "C10.2", "C10.3",
                        "C10.4", "C10.8", "C10.9"],
        "rest_hypo":   ["C12"  , "C12.9",
                        "C13.0", "C13.1", "C13.2", "C13.8", "C13.9"],
        "glottis":     ["C32.0"],
        "rest_larynx": ["C32.1", "C32.2", "C32.3", "C32.8", "C32.9"],
        "tongue":      ["C02.0", "C02.1", "C02.2", "C02.3", "C02.4", "C02.8",
                        "C02.9",],
        "gum_cheek":   ["C03.0", "C03.1", "C03.9", "C06.0", "C06.1", "C06.2",
                        "C06.8", "C06.9",],
        "mouth_floor": ["C04.0", "C04.1", "C04.8", "C04.9",],
        "palate":      ["C05.0", "C05.1", "C05.2", "C05.8", "C05.9",],
        "glands":      ["C08.0", "C08.1", "C08.9",],
    }
    SUBSITE_LIST = [icd for icd_list in SUBSITE_DICT.values() for icd in icd_list]

    subsite = models.CharField(max_length=10, choices=SUBSITES)
    """The subsite is a more granular categorization by the anatomical region
    of the head and neck where the primary tumor occurs in. It is usually
    encoded using the ICD-10 codes."""

    central = models.BooleanField(blank=True, null=True)
    """Is the tumor symmetric w.r.t. the patients mid-sagittal line?"""

    extension = models.BooleanField(blank=True, null=True)
    """Does the tumor cross the mid-sagittal line of the patient?"""

    volume = models.FloatField(blank=True, null=True)
    """Volume of the patient's tumor."""

    t_stage = models.PositiveSmallIntegerField(choices=Patient.T_stages.choices)
    """Stage of the primary tumor. Categorized the tumor by size and
    infiltration of tissue types."""

    stage_prefix = models.CharField(max_length=1, choices=[("c", "c"),
                                                           ("p", "p")])
    """T-stage prefix: 'c' for 'clinical' and 'p' for 'pathological'."""

    def __str__(self):
        """Report some main characteristics."""
        return f"#{self.pk}: T{self.t_stage} tumor of patient #{self.patient.pk}"

    def save(self, *args, **kwargs):
        """
        Before creating the database entry, determine the location of the
        tumor from the specified subsite and update the patient it is assigned
        to, to the correct T-stage.
        """
        if self.patient.dataset.is_locked:
            msg = "Cannot edit tumor of patient in locked dataset"
            self.logger.error(msg)
            raise DatasetIsLocked(msg)

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
            self.logger.warning(
                "Could not extract location for this tumor's "
                f"({self}) subsite ({self.get_subsite_display()})"
            )

        tmp = super(Tumor, self).save(*args, **kwargs)

        # call patient's `update_t_stage` method
        self.patient.update_t_stage()

        return tmp

    def delete(self, *args, **kwargs):
        """
        Block if patient's dataset is locked. And upon deletion, update the
        patient's T-stage.
        """
        if self.patient.dataset.is_locked:
            msg = "Cannot delete tumor of patient in locked dataset"
            self.logger.error(msg)
            raise DatasetIsLocked(msg)

        patient = self.patient
        tmp = super(Tumor, self).delete(*args, **kwargs)
        patient.update_t_stage()
        return tmp


Mod = namedtuple("Mod", "value label spec sens")

class Diagnose(ModelLoggerMixin, models.Model):
    """
    Model describing the diagnosis of one side of a patient's neck with
    regard to their lymphaitc metastatic involvement.
    """

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    """This defines the connection to the `Patient` model."""

    class MetaModality(type):
        """
        Meta class for providing the classmethod attributes to the
        `Modalities` class similar to what Django's enum types have.
        """
        def __init__(cls, classname, bases, classdict, *args, **kwargs):
            cls._mods = []
            for key, val in classdict.items():
                if (
                    not key.startswith("_")
                    and not callable(val)
                    and all([c.isupper() for c in key])
                ):
                    cls._mods.append(val)

            super().__init__(classname, bases, classdict, *args, **kwargs)

        def __len__(cls):
            return len(cls._mods)

        def __iter__(cls):
            cls._i = 0
            return cls

        def __next__(cls):
            if cls._i < len(cls):
                mod = cls._mods[cls._i]
                cls._i += 1
                return mod
            else:
                raise StopIteration

        @property
        def choices(cls):
            """Return list of tuples suitable for the
            ``django.db.models.ChoiceField``"""
            return [(mod.value, mod.label) for mod in cls._mods]

        @property
        def values(cls):
            """Database values the modality field can take on."""
            return [mod.value for mod in cls._mods]

        @property
        def labels(cls):
            """Human readable labels for the values of the modality field."""
            return [mod.label for mod in cls._mods]

        @property
        def spsn(cls):
            """Sensitiviy & specificity of the implemented modalities."""
            return [[mod.spec, mod.sens] for mod in cls._mods]

    class Modalities(metaclass=MetaModality):
        """
        Class that aims to replicate the functionality of ``TextChoices``
        from Django's enum types, but with the added functionality of storing
        the sensitivity & specificity of the respective modality.
        """
        CT   = Mod("CT" ,                  "CT" ,                    0.76, 0.81)
        MRI  = Mod("MRI",                  "MRI",                    0.63, 0.81)
        PET  = Mod("PET",                  "PET",                    0.86, 0.79)
        FNA  = Mod("FNA",                  "Fine Needle Aspiration", 0.98, 0.80)
        DC   = Mod("diagnostic_consensus", "Diagnostic Consensus"  , 0.86, 0.81)
        PATH = Mod("pathology",            "Pathology",              1.  , 1.  )
        PCT  = Mod("pCT",                  "Planning CT",            0.86, 0.81)

    modality = models.CharField(max_length=20, choices=Modalities.choices)
    """The diagnostic modality that was used to reach the diagnosis."""
    #:
    diagnose_date = RobustDateField(blank=True, null=True)
    #: diagnosed side
    side = models.CharField(max_length=10, choices=[("ipsi", "ipsi"),
                                                    ("contra", "contra")])

    LNLs = [
        "I", "Ia" , "Ib", "II", "IIa", "IIb", "III", "IV", "V", "Va", "Vb", "VII"
    ]
    """List of implemented lymph node levels. When the `models` module is
    imported, a simple for-loop creates additional fields for the `Diagnose`
    class for each of the elements in this list."""

    def __str__(self):
        """Report some info for admin view."""
        return (f"#{self.pk}: {self.get_modality_display()} diagnose "
                f"({self.side}) of patient #{self.patient.pk}")

    def save(self, *args, **kwargs):
        """
        Frist, check that the dataset the respective patient belongs to is not
        locked.

        Then make sure LNLs and their sublevels (e.g. 'a' and 'b') are treated
        consistelntly. E.g. when sublevel ``Ia`` is reported to be involved,
        the involvement status of level ``I`` cannot be reported as healthy.

        Also, if all LNLs are reported as unknown (``None``), just delete it.
        """
        if self.patient.dataset.is_locked:
            msg = "Cannot edit diagnose of patient in locked dataset"
            self.logger.error(msg)
            raise DatasetIsLocked(msg)

        if all([getattr(self, lnl) is None for lnl in self.LNLs]):
            super().save(*args, **kwargs)
            return self.delete()

        safe_negate = lambda x: False if x is None else not x

        # LNL I (a and b)
        if self.Ia or self.Ib:
            self.I = True
        elif safe_negate(self.Ia) and safe_negate(self.Ib):
            self.I = False

        # LNL II (a and b)
        if self.IIa or self.IIb:
            self.II = True
        elif safe_negate(self.IIa) and safe_negate(self.IIb):
            self.II = False

        # LNL V (a and b)
        if self.Va or self.Vb:
            self.V = True
        elif safe_negate(self.Va) and safe_negate(self.Vb):
            self.V = False

        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Block diagnose deletion if patient's dataset is locked."""
        if self.patient.dataset.is_locked:
            msg = "Cannot delete diagnose of patient in locked dataset"
            self.logger.error(msg)
            raise DatasetIsLocked(msg)

        return super().delete(*args, **kwargs)


# add lymph node level fields to model 'Diagnose'
for lnl in Diagnose.LNLs:
    Diagnose.add_to_class(lnl, models.BooleanField(blank=True, null=True))

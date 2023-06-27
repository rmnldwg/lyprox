"""
This module defines how patient related models work and how they interact with each
other. Currently, four models are implemented: The `Dataset`, `Patient`, `Tumor`
and the `Diagnose`. A `Dataset` groups `Patient` entries and associates them with an
`Institution`, while also providing methods for importing and exporting from and to CSV
file.

A `Patient` holds demographic and relational information about each recorded patient.
The respective entry can have multiple `Tumor` and `Diagnose` entries associated with
it, which is defined by the ``django.db.models.ForeignKey`` attribute in the `Tumor`
and `Diagnose` class.

There are also custom methods implemented, making sure that e.g. the diagnosis
of a sublevel (lets say ``Ia``) is consistent with the diagnosis of the
respective superlevel (in that case ``I``).
"""
# pylint: disable=no-member
# pylint: disable=logging-fstring-interpolation

import logging
from collections import namedtuple

import dateparser
import pandas as pd
from django.db import models
from django.forms import ValidationError
from django.urls import reverse
from github import UnknownObjectException

from lyprox import loggers
from lyprox.accounts.models import Institution
from lyprox.patients import ioports, mixins
from lyprox.patients.fields import RobustDateField
from lyprox.settings import GITHUB

logger = logging.getLogger(name=__name__)


class LockedDatasetError(Exception):
    """Raised when a `Dataset` or an associated entry was tried to be edited."""


class CorruptedDatasetError(Exception):
    """Raised when there is reason to believe that the dataset is corrupted."""


class Dataset(loggers.ModelLoggerMixin, models.Model):
    """A collection of patients, usually importet from a CSV file in a GitHub repo.

    When created, this model fetches the CSV file from the GitHub repo and adds the
    `Patient` entries to the database. It also creates the realted `Tumor` and
    `Diagnose` entries.
    """
    git_repo_owner = models.CharField(max_length=50, default="rmnldwg")
    """Owner of the GitHub repository that contains the dataset."""
    git_repo_name = models.CharField(max_length=50, default="lydata.test")
    """Name of the GitHub repository that contains the dataset."""
    revision = models.CharField(max_length=40, default="main")
    """Git revision in which to search for the data. E.g., a commit hash, or tag."""
    data_path = models.CharField(max_length=100, default="2021-usz-oropharynx/data.csv")
    """Path to the CSV file containing the patient data inside the git repo."""
    data_url = models.URLField(max_length=400)
    """URL to the CSV file in the GitHub repo."""
    data_sha = models.CharField(max_length=40)
    """SHA of the CSV file in the GitHub repo."""
    institution = models.ForeignKey(to=Institution, on_delete=models.CASCADE)
    """The institution that provided the dataset."""
    is_locked = models.BooleanField(default=False)
    """Whether the dataset is locked or not. Locked datasets cannot be edited."""
    is_public = models.BooleanField(default=False)
    """Whether the dataset is public or not. Public datasets can be viewed by everyone."""
    date_created = models.DateTimeField()
    """Date and time when the dataset was created."""
    is_outdated = models.BooleanField(default=False)
    """Whether the data file has been updated since the last import."""


    class Meta:
        unique_together = ("git_repo_owner", "git_repo_name", "data_path")


    def __str__(self):
        return f"{self.institution.shortname}: {self.git_repo_id}"

    @property
    def name(self):
        """Return the name of the dataset."""
        return self.data_path.replace("/data.csv", "").split("-")[-1]

    @property
    def git_repo_id(self):
        """Return the ID of the GitHub repository."""
        return f"{self.git_repo_owner}/{self.git_repo_name}"

    @property
    def git_repo_url(self):
        """Return the URL of the GitHub repository."""
        return f"https://github.com/{self.git_repo_id}"

    @property
    def patient_count(self) -> int:
        """Return the number of patients in the dataset."""
        return Patient.objects.filter(dataset=self).count()


    def compute_fields(
        self,
        git_repo_url: str,
        revision: str,
        data_path: str,
        user_institution: Institution,
        **_kwargs,
    ) -> None:
        """Dynamically compute fields from the GitHub repository."""
        repo_id = git_repo_url.split("github.com/")[-1]
        self.git_repo_owner, self.git_repo_name = repo_id.split("/")

        repo = self.fetch_repo()
        self.date_created = dateparser.parse(repo.pushed_at)
        self.is_public = not repo.private

        self.revision = revision
        self.data_path = data_path

        data_file = self.fetch_file()
        self.data_sha = data_file.sha
        self.data_url = data_file.download_url
        table = self.fetch_dataframe()
        self.institution = self.get_institution(table, fallback=user_institution)


    @staticmethod
    def get_institution(table: pd.DataFrame, fallback: Institution) -> Institution:
        """Return the institution that provided the dataset."""
        try:
            institution_name = table["patient", "#", "institution"].unique()[0]
            return Institution.objects.get(name=institution_name)
        except KeyError:
            return fallback


    def fetch_repo(self):
        """Return the GitHub repository object."""
        if hasattr(self, "_repo"):
            return self._repo

        try:
            self._repo = GITHUB.get_repo(f"{self.git_repo_owner}/{self.git_repo_name}")
        except UnknownObjectException as unk_obj_exc:
            raise ValidationError(
                f"Could not find repository {self.git_repo_owner}/{self.git_repo_name}."
            ) from unk_obj_exc

        return self._repo


    def fetch_file(self):
        """Return the GitHub file object."""
        if hasattr(self, "_file"):
            return self._file

        repo = self.fetch_repo()
        try:
            self._file = repo.get_contents(self.data_path, ref=self.revision)
        except UnknownObjectException as unk_obj_exc:
            raise ValidationError(
                f"Could not find file {self.data_path} in repository "
                f"{self.git_repo_owner}/{self.git_repo_name}."
            ) from unk_obj_exc

        return self._file


    def check_itegrity(self):
        """Check whether the dataset is still consistent with the GitHub repo."""
        pushed_at = dateparser.parse(self.fetch_repo().pushed_at)
        data_sha = self.fetch_file().sha

        is_repo_modfied = pushed_at > self.date_created
        is_sha_changed = data_sha != self.data_sha

        if is_repo_modfied and is_sha_changed:
            self.logger.warning("Data file has been updated since last import.")
            self.is_outdated = True
            self.save(override=True)

        if not is_repo_modfied and is_sha_changed:
            raise CorruptedDatasetError(
                "Data file SHA of locked dataset does not match SHA of file "
                "in GitHub repo. This should never happen."
            )


    def fetch_readme(self) -> str:
        """Return the README.md file of the dataset as a string."""
        if not hasattr(self, "_readme"):
            relative_readme_path = self.data_path.replace("data.csv", "README.md")

            try:
                self._readme = self.fetch_repo().get_contents(
                    relative_readme_path,
                    ref=self.revision,
                ).decoded_content.decode("utf-8")
            except UnknownObjectException as _e:
                self._readme = "No README.md file found."

        return self._readme


    def fetch_dataframe(self) -> pd.DataFrame:
        """Return the dataset as a pandas DataFrame."""
        return pd.read_csv(self.data_url, header=[0, 1, 2])


    def lock(self):
        """Lock the dataset, so that it cannot be edited anymore."""
        self.is_locked = True
        self.save(override=True)


    def unlock(self):
        """Unlock the dataset, so that it can be edited again."""
        self.is_locked = False
        self.save(override=True)


    def save(self, *args, override: bool = False, **kwargs):
        """Save the model instance to the database.

        Rise an error if the dataset is locked and ``override`` is not set to ``True``.
        """
        if self.is_locked and not override:
            raise LockedDatasetError("Cannot edit locked dataset.")

        super().save(*args, **kwargs)


    def delete(self, *args, override: bool = False, **kwargs):
        """Delete the model instance from the database.

        Rise an error if the dataset is locked and ``override`` is not set to ``True``.
        """
        if self.is_locked and not override:
            raise LockedDatasetError("Cannot delete locked dataset.")

        super().delete(*args, **kwargs)


    def import_csv_to_db(self):
        """Import the dataset from the CSV file into the database.

        This method lock the dataset right afterwards to prevent editing the uploaded
        patients.
        """
        table = self.fetch_dataframe()
        num_new, num_skipped = ioports.import_from_pandas(table, self)
        self.logger.info(
            f"{num_new} new patients were added to dataset {self}. "
            f"{num_skipped} were skipped."
        )
        self.lock()


class Patient(mixins.LockedDatasetMixin, loggers.ModelLoggerMixin, models.Model):
    """
    The representation of a patient in the database.

    Contains some demographic information, as well as patient-specific characteristics
    that are important in the context of cancer, e.g. HPV status.

    This model also ties together the information about the patient's tumor(s)
    and the lymphatic progression pattern of that patient in the form of a
    `Diagnose` model.
    """
    # pylint: disable=invalid-name
    sex = models.CharField(
        max_length=10,
        choices=[("female", "female"), ("male", "male")],
    )
    """Biological sex of the patient."""

    age = models.IntegerField()
    """Age in years at the time of diagnosis."""

    diagnose_date = RobustDateField()
    """Date of histological confirmation with a squamous cell carcinoma."""

    alcohol_abuse = models.BooleanField(blank=True, null=True)
    """Was the patient a drinker?"""

    nicotine_abuse = models.BooleanField(blank=True, null=True)
    """Was the patient a smoker?"""

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

    t_stage = models.PositiveSmallIntegerField(choices=T_stages.choices, default=0)
    """Stage of the primary tumor. Categorized the tumor by size and
    infiltration of tissue types."""

    class N_stages(models.IntegerChoices):
        """Defines the possible N-stages as choice class."""
        N0 = 0, "N0"
        N1 = 1, "N1"
        N2 = 2, "N2"
        N3 = 3, "N3"

    n_stage = models.PositiveSmallIntegerField(choices=N_stages.choices, default=0)
    """Categorizes the extend of regional metastases."""

    class M_stages(models.IntegerChoices):
        """Defines the possible M-stages as choice class."""
        M0 = 0, "M0"
        M1 = 1, "M1"
        MX = 2, "MX"

    m_stage = models.PositiveSmallIntegerField(choices=M_stages.choices, default=0)
    """Indicates whether or not there are distant metastases."""

    dataset = models.ForeignKey(to=Dataset, on_delete=models.CASCADE)
    """Every patient must belong to a dataset entry that manages importing, exporting
    as well as preventing edits that compromise the integrity of the dataset."""

    def __str__(self):
        """Report some patient specifics."""
        return f"#{self.pk}: {self.sex} ({self.age})"

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
        """Update T-stage after new `Tumor` is added to `Patient`.

        This `Patient` method gets called in `Tumor.save` method. It also updates the
        patient's stage prefix to that of the tumor with the highest T-category.
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

    def validate_unique(self, exclude=None) -> None:
        """Make sure the patient has not already been added.

        Uniqueness is checked by ensuring this patient's combination of sex, age, date
        of diagnosis, alcohol, nicotine, and HPV status, as well as TNM stage is
        unique in the dataset.
        """
        unique_fields = [field.name for field in self.__class__._meta.fields]
        duplicate_does_exist = self.__class__.objects.filter(
            **{field: getattr(self, field) for field in unique_fields}
        ).exists()

        if duplicate_does_exist:
            raise ValidationError("Patient already exists in this dataset.")

        super().validate_unique(exclude)


class Tumor(mixins.LockedDatasetMixin, loggers.ModelLoggerMixin, models.Model):
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
        ("oral cavity", (
            ("C02"  , "other parts of tongue"),
            ("C02.0", "dorsal surface of tongue"),
            ("C02.1", "border of tongue"),
            ("C02.2", "ventral surface of tongue"),
            ("C02.3", "anterior two thirds of tongue"),
            ("C02.4", "lingual tonsil"),
            ("C02.8", "overlapping sites of tongue"),
            ("C02.9", "tongue, nos"),

            ("C03"  , "gum"),
            ("C03.0", "upper gum"),
            ("C03.1", "lower gum"),
            ("C03.9", "gum, nos"),

            ("C04"  , "floor of mouth"),
            ("C04.0", "anterior floor of mouth"),
            ("C04.1", "lateral floor of mouth"),
            ("C04.8", "overlapping lesion of floor of mouth"),
            ("C04.9", "floor of mouth, nos"),

            ("C05"  , "palate"),
            ("C05.0", "hard palate"),
            ("C05.1", "soft palate, nos"),
            ("C05.2", "uvula"),
            ("C05.8", "overlapping lesion of palate"),
            ("C05.9", "palate, nos"),

            ("C06"  , "other parts of mouth"),
            ("C06.0", "cheeck mucosa"),
            ("C06.1", "vestibule of mouth"),
            ("C06.2", "retromolar area"),
            ("C06.8", "overlapping lesion(s) of NOS parts of mouth"),
            ("C06.9", "mouth, nos"),

            ("C07"  , "parotid gland"),

            ("C08"  , "other major salivary glands"),
            ("C08.0", "submandibular gland"),
            ("C08.1", "sublingual gland"),
            ("C08.9", "salivary gland, nos"))
        ),
        ("oropharynx",  (
            ("C01"  , "base of tongue, nos"),

            ("C09"  , "tonsil"),
            ("C09.0", "tonsillar fossa"),
            ("C09.1", "tonsillar pillar"),
            ("C09.8", "overlapping lesion of tonsil"),
            ("C09.9", "tonsil, nos"),

            ("C10"  , "oropharynx"),
            ("C10.0", "vallecula"),
            ("C10.1", "anterior surface of epiglottis"),
            ("C10.2", "lateral wall of oropharynx"),
            ("C10.3", "posterior wall of oropharynx"),
            ("C10.4", "branchial cleft"),
            ("C10.8", "overlapping lesions of oropharynx"),
            ("C10.9", "oropharynx, nos"),)
        ),
        ("hypopharynx", (
            ("C12"  , "pyriform sinus"),

            ("C13"  , "hypopharynx"),
            ("C13.0", "postcricoid region"),
            ("C13.1", "hypopharyngeal aspect of aryepiglottic fold"),
            ("C13.2", "posterior wall of hypopharynx"),
            ("C13.8", "overlapping lesion of hypopharynx"),
            ("C13.9", "hypopharynx, nos"),)
        ),
        ("larynx",      (
            ("C32"  , "larynx"),
            ("C32.0", "glottis"),
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
        "tonsil":      ["C09"  , "C09.0", "C09.1", "C09.8", "C09.9"],
        "rest_oro":    ["C10"  , "C10.0", "C10.1", "C10.2", "C10.3",
                        "C10.4", "C10.8", "C10.9"],
        "rest_hypo":   ["C12"  , "C12.9",
                        "C13"  , "C13.0", "C13.1", "C13.2", "C13.8", "C13.9"],
        "glottis":     ["C32"  , "C32.0"],
        "rest_larynx": ["C32.1", "C32.2", "C32.3", "C32.8", "C32.9"],
        "tongue":      ["C02"  , "C02.0", "C02.1", "C02.2", "C02.3", "C02.4", "C02.8",
                        "C02.9",],
        "gum_cheek":   ["C03"  , "C03.0", "C03.1", "C03.9",
                        "C06"  , "C06.0", "C06.1", "C06.2", "C06.8", "C06.9",],
        "mouth_floor": ["C04"  , "C04.0", "C04.1", "C04.8", "C04.9",],
        "palate":      ["C05"  , "C05.0", "C05.1", "C05.2", "C05.8", "C05.9",],
        "glands":      ["C08"  , "C08.0", "C08.1", "C08.9",],
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
        # Automatically extract location from subsite
        subsite_dict = dict(self.SUBSITES)
        location_list = self.Locations.values

        found_location = False
        for loc in location_list:
            icd_codes = [tpl[0] for tpl in subsite_dict[loc]]
            found_location = any(
                self.subsite in code or code in self.subsite for code in icd_codes
            )
            if found_location:
                self.location = loc
                break

        if not found_location:
            self.logger.warning(
                "Could not extract location for this tumor's "
                f"({self}) subsite ({self.get_subsite_display()})"
            )

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


Mod = namedtuple("Mod", "value label spec sens")

class Diagnose(mixins.LockedDatasetMixin, loggers.ModelLoggerMixin, models.Model):
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
            cls._start = 0
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
            current = cls._start
            while current < len(cls):
                yield cls._mods[current]
                current += 1

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
        Make sure LNLs and their sublevels (e.g. 'a' and 'b') are treated
        consistelntly. E.g. when sublevel ``Ia`` is reported to be involved,
        the involvement status of level ``I`` cannot be reported as healthy.

        Also, if all LNLs are reported as unknown (``None``), just delete it.
        """
        # pylint: disable=attribute-defined-outside-init
        # pylint: disable=invalid-name
        if all(getattr(self, lnl) is None for lnl in self.LNLs):
            super().save(*args, **kwargs)
            return self.delete()

        def safe_negate(val):
            if val is None:
                return False
            return not val

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


# add lymph node level fields to model 'Diagnose'
for lnl in Diagnose.LNLs:
    Diagnose.add_to_class(lnl, models.BooleanField(blank=True, null=True))

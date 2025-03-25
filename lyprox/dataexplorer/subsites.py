"""Tumor subsites as ICD-10 codes with the respective names."""

from django.db import models


def convert_camel_to_snake(name: str) -> str:
    """Convert camel case to snake case.

    >>> convert_camel_to_snake("BaseOfTongue")
    'base_of_tongue'
    >>> convert_camel_to_snake("DorsalSurfaceOfTongue")
    'dorsal_surface_of_tongue'
    """
    return "".join(["_" + c.lower() if c.isupper() else c for c in name]).lstrip("_")


class Subsites:
    """All tumor subsites as ICD-10 codes with the respective names.

    This container class for all the subsite ICD enums provides the convenience of
    accessing all subsites in a single place. One may use it as follows:
    >>> Subsites.Tongue.C02_0.label
    'Dorsal surface of tongue'
    >>> Subsites.Gum.choices   # doctest: +NORMALIZE_WHITESPACE
    [('C03', 'Gum'),
     ('C03.0', 'Upper gum'),
     ('C03.1', 'Lower gum'),
     ('C03.9', 'Gum, unspecified')]
    >>> Subsites.all_values()   # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    ['C01', 'C01.9', ..., 'C32.9']
    """

    class BaseOfTongue(models.TextChoices):
        """Tumor subsites in the base of the tongue."""

        C01 = "C01", "Base of Tongue"
        C01_9 = "C01.9", "Base of Tongue"  # invalid ICD-10 code, but often used

    class Tongue(models.TextChoices):
        """Tumor subsites in the tongue."""

        C02 = "C02", "Tongue"
        C02_0 = "C02.0", "Dorsal surface of tongue"
        C02_1 = "C02.1", "Border of tongue"
        C02_2 = "C02.2", "Ventral surface of tongue"
        C02_3 = "C02.3", "Anterior two-thirds of tongue"
        C02_4 = "C02.4", "Lingual tonsil"
        C02_8 = "C02.8", "Overlapping lesion of tongue"
        C02_9 = "C02.9", "Tongue, unspecified"

    class Gum(models.TextChoices):
        """Tumor subsites in the gums."""

        C03 = "C03", "Gum"
        C03_0 = "C03.0", "Upper gum"
        C03_1 = "C03.1", "Lower gum"
        C03_9 = "C03.9", "Gum, unspecified"

    class FloorOfMouth(models.TextChoices):
        """Tumor subsites in the floor of the mouth."""

        C04 = "C04", "Floor of Mouth"
        C04_0 = "C04.0", "Anterior floor of mouth"
        C04_1 = "C04.1", "Lateral floor of mouth"
        C04_8 = "C04.8", "Overlapping lesion of floor of mouth"
        C04_9 = "C04.9", "Floor of mouth, unspecified"

    class Palate(models.TextChoices):
        """Tumor subsites in the palate."""

        C05 = "C05", "Palate"
        C05_0 = "C05.0", "Hard palate"
        C05_1 = "C05.1", "Soft palate"
        C05_2 = "C05.2", "Uvula"
        C05_8 = "C05.8", "Overlapping lesion of palate"
        C05_9 = "C05.9", "Palate, unspecified"

    class Cheek(models.TextChoices):
        """Tumor subsites in the gums and cheeks."""

        C06 = "C06", "Other and unspecified parts of mouth"
        C06_0 = "C06.0", "Cheek mucosa"
        C06_1 = "C06.1", "Vestibule of mouth"
        C06_2 = "C06.2", "Retromolar area"
        C06_8 = "C06.8", "Overlapping lesion of other and unspecified parts of mouth"
        C06_9 = "C06.9", "Mouth, unspecified"

    # class Glands(models.TextChoices):
    #     """Tumor subsites in the glands."""
    #     C08   = "C08"  , "Salivary glands"
    #     C08_0 = "C08.0", "Submandibular gland"
    #     C08_1 = "C08.1", "Sublingual gland"
    #     C08_9 = "C08.9", "Major salivary gland, unspecified"

    class Tonsil(models.TextChoices):
        """Tumor subsites in the tonsils."""

        C09 = "C09", "Tonsil"
        C09_0 = "C09.0", "Tonsillar fossa"
        C09_1 = "C09.1", "Tonsillar pillar (anterior)(posterior)"
        C09_8 = "C09.8", "Overlapping lesion of tonsil"
        C09_9 = "C09.9", "Tonsil, unspecified"

    class Oropharynx(models.TextChoices):
        """Tumor subsites in the rest of the oropharynx."""

        C10 = "C10", "Oropharynx"
        C10_0 = "C10.0", "Vallecula"
        C10_1 = "C10.1", "Anterior surface of epiglottis"
        C10_2 = "C10.2", "Lateral wall of oropharynx"
        C10_3 = "C10.3", "Posterior wall of oropharynx"
        C10_4 = "C10.4", "Branchial cleft"
        C10_8 = "C10.8", "Overlapping lesion of oropharynx"
        C10_9 = "C10.9", "Oropharynx, unspecified"

    class Hypopharynx(models.TextChoices):
        """Tumor subsites in the rest of the hypopharynx."""

        C12 = "C12", "Piriform sinus"
        C12_9 = "C12.9", "Piriform sinus"  # invalid ICD-10 code, but often used
        C13 = "C13", "Hypopharynx"
        C13_0 = "C13.0", "Postcricoid region"
        C13_1 = "C13.1", "Aryepiglottic fold, hypopharyngeal aspect"
        C13_2 = "C13.2", "Posterior wall of hypopharynx"
        C13_8 = "C13.8", "Overlapping lesion of hypopharynx"
        C13_9 = "C13.9", "Hypopharynx, unspecified"

    class Larynx(models.TextChoices):
        """Tumor subsites in the rest of the larynx."""

        C32 = "C32", "Larynx"
        C32_0 = "C32.0", "Glottis"
        C32_1 = "C32.1", "Supraglottis"
        C32_2 = "C32.2", "Subglottis"
        C32_3 = "C32.3", "Laryngeal cartilage"
        C32_8 = "C32.8", "Overlapping lesion of larynx"
        C32_9 = "C32.9", "Larynx, unspecified"

    @classmethod
    def get_subsite_enums(cls) -> dict[str, models.enums.ChoicesMeta]:
        """Return a dictionary of all subsite enums.

        Note that the keys are the subsite names in snake case. E.g., ``BaseOfTongue``
        would become ``base_of_tongue``. This is done by the `convert_camel_to_snake`
        helper function.

        >>> Subsites.get_subsite_enums().keys()   # doctest: +NORMALIZE_WHITESPACE
        dict_keys(['base_of_tongue', 'tongue', 'gum', 'floor_of_mouth', 'palate',
                   'cheek', 'glands', 'tonsil', 'oropharynx', 'hypopharynx', 'larynx'])
        """
        return {
            convert_camel_to_snake(name): value
            for name, value in cls.__dict__.items()
            if (
                not name.startswith("_") and isinstance(value, models.enums.ChoicesMeta)
            )
        }

    @classmethod
    def all_choices(cls) -> list[tuple[str, str]]:
        """Return concatenated choices list of all subsites."""
        choices = []
        for subsite in cls.get_subsite_enums().values():
            choices.extend(subsite.choices)
        return choices

    @classmethod
    def all_values(cls) -> list[str]:
        """Return concatenated values list of all subsites."""
        values = []
        for subsite in cls.get_subsite_enums().values():
            values.extend(subsite.values)
        return values

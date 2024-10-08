"""The `dataexplorer.forms` module defines the relatively complex form that is
used for querying the database later.

It also implements some custom form elements, like `ThreeWayToggle` and
`ThreeWayToggleWidget` that represent the custom logic and appearance of a
three-way toggle button respectively, which appears numerous times in the
Dashboard interface.

Finally, a custom ``MultipleChoice`` field of somewhat unnecessary complexity
is implemented here that allows us to select the institutions from which the
ptients should be included via check boxes with the institution logo on it.
"""

# pylint: disable=no-member
import logging

from django import forms
from django.core.exceptions import ValidationError

from ..loggers import FormLoggerMixin
from ..patients.models import Dataset, Diagnose, Patient, Tumor

logger = logging.getLogger(__name__)


def trio_to_bool(value: int):
    """Transform -1, 0, and +1 to False, None and True respectively.

    Any other values are simply passed through unchanged. This is used to map the
    values of the three-way toggle buttons to its boolean representation.
    """
    if value == 1:
        return True
    if value == -1:
        return False
    if value == 0:
        return None

    return value


class ThreeWayToggleWidget(forms.RadioSelect):
    """Widget that renders the three-way toggle button and allows to set the
    attributes of the individual inputs (radio buttons) as `option_attrs` as
    well as the attributes of the container as ``attrs``.
    """

    template_name = "widgets/three_way_toggle.html"
    option_template_name = "widgets/three_way_toggle_option.html"
    option_attrs = {"class": "radio is-hidden", "onchange": "changeHandler();"}

    def __init__(
        self, attrs=None, choices=(), option_attrs=None, label=None, tooltip=None
    ):
        """Store arguments and option attributes for later use."""
        self.label = label
        self.tooltip = tooltip
        self.option_attrs = {
            "class": "radio is-hidden",
            "onchange": "changeHandler();",
            **(option_attrs or {}),
        }
        super().__init__(attrs, choices)

    def get_context(self, name, value, attrs):
        """Pass label and tooltip to the context variable"""
        context = super().get_context(name, value, attrs)
        context["widget"]["label"] = self.label
        context["widget"]["tooltip"] = self.tooltip
        return context

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        """Pass the option attributes to the actual options"""
        return super().create_option(
            name,
            value,
            label,
            selected,
            index,
            subindex,
            attrs=self.build_attrs(self.option_attrs, attrs),
        )


class ThreeWayToggle(forms.ChoiceField):
    """A toggle switch than can be in three different states: Positive/True,
    unkown/None and negative/False.
    """

    def __init__(
        self,
        attrs=None,
        option_attrs=None,
        label=None,
        tooltip=None,
        choices=None,
        initial=0,
        required=False,
        **kwargs,
    ):
        """Pass the arguments, like `label` and `tooltip` to the constructor
        of the custom widget.
        """
        if choices is None:
            choices = [(1, "plus"), (0, "ban"), (-1, "minus")]

        if len(choices) != 3:
            raise ValueError("Three-way toggle button must have three choices")

        super().__init__(
            widget=ThreeWayToggleWidget(
                attrs=attrs, option_attrs=option_attrs, label=label, tooltip=tooltip
            ),
            choices=choices,
            initial=initial,
            required=required,
            **kwargs,
        )

    def to_python(self, value):
        """Cast the string to an integer."""
        try:
            return int(value)
        except ValueError:
            return value
        except TypeError as type_err:
            raise ValidationError("Expects a number") from type_err


class DatasetModelChoiceIndexer:
    """Custom class with which one can access additional information from
    the model that is chosen by the `DatasetMultipleChoiceField`.
    """

    def __init__(self, field) -> None:
        self.field = field
        self.queryset = field.queryset

    def __getitem__(self, key):
        obj = self.queryset[key]
        return self.info(obj)

    def info(self, obj: Dataset) -> tuple[int, str]:
        """Return the label and logo URL for the Dataset."""
        return (
            self.field.label_from_instance(obj),
            self.field.logo_url_from_instance(obj),
        )


class DatasetMultipleChoiceField(forms.ModelMultipleChoiceField):
    """Customize label description and add method that returns the logo URL for
    Datasets. The implementation is inspired by how the ``choices`` are
    implemented. But since some other functionality depends on how those
    choices are implemented, it cannot be changed easily.
    """

    name_and_url_indexer = DatasetModelChoiceIndexer
    """Allows one to extract more info (name and logo) about the objects."""

    def label_from_instance(self, obj: Dataset) -> str:
        """Dataset name as label."""
        return obj.__str__()

    def logo_url_from_instance(self, obj: Dataset) -> str:
        """Return URL of Dataset's logo."""
        return obj.institution.logo.url

    @property
    def names_and_urls(self):
        return self.name_and_url_indexer(self)


class DashboardForm(FormLoggerMixin, forms.Form):
    """Form for querying the database."""

    # select modalities to show
    modalities = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={
                "class": "checkbox is-hidden",
                "onchange": "changeHandler();",
            },
        ),
        choices=Diagnose.Modalities.choices,
        initial=["CT", "MRI", "PET", "FNA", "diagnostic_consensus", "pathology", "pCT"],
    )
    modality_combine = forms.ChoiceField(
        widget=forms.Select(attrs={"onchange": "changeHandler();"}),
        choices=[
            ("AND", "AND"),
            ("OR", "OR"),
            ("maxLLH", "maxLLH"),
            ("RANK", "RANK"),
        ],
        label="Combine",
        initial="maxLLH",
    )

    # patient specific fields
    nicotine_abuse = ThreeWayToggle(
        label="smoking status", tooltip="Select smokers or non-smokers"
    )
    hpv_status = ThreeWayToggle(
        label="HPV status", tooltip="Select patients being HPV positive or negative"
    )
    neck_dissection = ThreeWayToggle(
        label="neck dissection",
        tooltip="Include patients that have (or have not) received neck dissection",
    )
    n_status = ThreeWayToggle(
        label="N+ vs N0", tooltip="Select all N+ (or N0) patients"
    )
    dataset__in = DatasetMultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(
            # doesn't do anything since it's written by hand
            attrs={
                "class": "checkbox is-hidden",
                "onchange": "changeHandler();",
            },
        ),
        queryset=Dataset.objects.all().filter(is_public=True),
        initial=Dataset.objects.all().filter(is_public=True),
    )

    # tumor specific info
    subsite_oropharynx = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={
                "class": "checkbox is-hidden",
                "onchange": "changeHandler();",
            },
        ),
        choices=[
            ("base", "base of tongue"),  # choices here must match entries
            ("tonsil", "tonsil"),  # in the Tumor.SUBSITE_DICT keys
            ("rest_oro", "other"),
        ],
        initial=["base", "tonsil", "rest_oro"],
    )
    subsite_hypopharynx = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={
                "class": "checkbox is-hidden",
                "onchange": "changeHandler();",
            },
        ),
        choices=[("rest_hypo", "all")],  # choices here must match entries in
        initial=["rest_hypo"],  # the Tumor.SUBSITE_DICT keys
    )
    subsite_larynx = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={
                "class": "checkbox is-hidden",
                "onchange": "changeHandler();",
            },
        ),
        choices=[
            ("glottis", "glottis"),  # choices here must match entries
            ("supraglottis", "supraglottis"),  # in the Tumor.SUBSITE_DICT keys
            ("subglottis", "subglottis"),
            ("rest_larynx", "other"),
        ],
        initial=["glottis", "supraglottis", "subglottis", "rest_larynx"],
    )
    subsite_oral_cavity = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={
                "class": "checkbox is-hidden",
                "onchange": "changeHandler();",
            },
        ),
        choices=[
            ("tongue", "tongue"),  # choices here must match entries
            ("gum_cheek", "gums and cheek"),  # in the Tumor.SUBSITE_DICT keys
            ("mouth_floor", "floor of mouth"),
            ("palate", "palate"),
            ("glands", "salivary glands"),
        ],
        initial=["tongue", "gum_cheek", "mouth_floor", "palate", "glands"],
    )

    t_stage__in = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={
                "class": "checkbox is-hidden",
                "onchange": "changeHandler();",
            },
        ),
        choices=Patient.T_stages.choices,
        initial=[0, 1, 2, 3, 4],
    )
    central = ThreeWayToggle(
        label="central", tooltip="Choose to in- or exclude patients with central tumors"
    )
    extension = ThreeWayToggle(
        label="midline extension",
        tooltip=(
            "Investigate patients with tumors that do (or do not) "
            "cross the mid-sagittal line"
        ),
    )

    # checkbutton for switching to percent
    show_percent = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.widgets.RadioSelect(
            attrs={"class": "radio is-hidden", "onchange": "changeHandler();"},
            choices=[(True, "percent"), (False, "absolute")],
        ),
    )

    def __init__(self, *args, user, **kwargs):
        """Extend default initialization to create lots of fields for the
        LNLs from a list and hide some datasets for unauthenticated users.
        """
        super().__init__(*args, **kwargs)

        # dynamically define which datasets should be selectable
        if user.is_authenticated:
            self.fields["dataset__in"].queryset = Dataset.objects.all()
            self.fields["dataset__in"].initial = Dataset.objects.all()

        # add all LNL ToggleButtons so I don't have to write a myriad of them
        for side in ["ipsi", "contra"]:
            for lnl in Diagnose.LNLs:
                if lnl in ["I", "II", "V"]:
                    self.fields[f"{side}_{lnl}"] = ThreeWayToggle(
                        option_attrs={"onclick": "bothClickHandler(this)"}
                    )
                elif lnl in ["Ia", "Ib", "IIa", "IIb", "Va", "Vb"]:
                    self.fields[f"{side}_{lnl}"] = ThreeWayToggle(
                        option_attrs={"onclick": "subClickHandler(this)"}
                    )
                else:
                    self.fields[f"{side}_{lnl}"] = ThreeWayToggle()

    def clean(self):
        """Make sure LNLs I & II have correct values corresponding to their
        sublevels a & b. Also convert tstages from list of str to list of int.
        """
        cleaned_data = super(DashboardForm, self).clean()

        # necessary to prevent errors from processing invalid data
        if len(self.errors) != 0:
            return {}

        # map all -1,0,1 fields to False,None,True
        cleaned_data = {key: trio_to_bool(value) for key, value in cleaned_data.items()}

        # make sure LNLs I & II aren't in conflict with their sublevels
        for side in ["ipsi", "contra"]:
            for lnl in ["I", "II"]:
                a = cleaned_data[f"{side}_{lnl}a"]
                b = cleaned_data[f"{side}_{lnl}b"]

                # make sure data regarding sublevels is not conflicting
                if a is True or b is True:
                    cleaned_data[f"{side}_{lnl}"] = True
                if a is False and b is False:
                    cleaned_data[f"{side}_{lnl}"] = False

        # map `central` from False,None,True to the respective list of sides
        if cleaned_data["central"] is True:
            cleaned_data["side__in"] = ["central"]
        elif cleaned_data["central"] is False:
            cleaned_data["side__in"] = ["left", "right"]
        else:
            cleaned_data["side__in"] = ["left", "right", "central"]

        # map subsites 'base','tonsil','rest' to list of ICD codes.
        subsites = (
            cleaned_data["subsite_oropharynx"]
            + cleaned_data["subsite_hypopharynx"]
            + cleaned_data["subsite_larynx"]
            + cleaned_data["subsite_oral_cavity"]
        )

        icd_codes = []
        for sub in subsites:
            icd_codes += Tumor.SUBSITE_DICT[sub]
        cleaned_data["subsite__in"] = icd_codes

        # make sure T-stages are list of ints
        str_list = cleaned_data["t_stage__in"]
        cleaned_data["t_stage__in"] = [int(s) for s in str_list]

        self.logger.debug(f"cleaned data: {cleaned_data}")
        return cleaned_data

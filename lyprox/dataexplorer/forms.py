"""
The `dataexplorer.forms` module defines the relatively complex form that is
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
from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from lydata.utils import get_default_modalities

from lyprox.dataexplorer.subsites import Subsites
from lyprox.dataexplorer.loader import DataInterface
from lyprox.loggers import FormLoggerMixin
from lyprox.settings import LNLS, TStages

logger = logging.getLogger(__name__)


def trio_to_bool(value: int | Any) -> bool | Any:
    """
    Transform -1, 0, and +1 to False, None and True respectively.

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


def format_dataset_choices(datasets: list[str]) -> list[tuple[str, str]]:
    """Create a list of tuples for the dataset choices."""
    choices = []
    for dataset in datasets:
        year, institution, subsite = dataset.split("-", maxsplit=2)
        label = f"{year} {institution.upper()} {subsite.capitalize()}"
        choices.append((dataset, label))

    return choices


class ThreeWayToggleWidget(forms.RadioSelect):
    """
    Widget that renders the three-way toggle button and allows to set the
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
        """Pass label and tooltip to the context variable."""
        context = super().get_context(name, value, attrs)
        context["widget"]["label"] = self.label
        context["widget"]["tooltip"] = self.tooltip
        return context

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        """Pass the option attributes to the actual options."""
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
    """
    A toggle switch than can be in three different states: Positive/True,
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
        """
        Pass the arguments, like `label` and `tooltip` to the constructor
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


checkbox_attrs = {"class": "checkbox is-hidden", "onchange": "changeHandler();"}


class DashboardForm(FormLoggerMixin, forms.Form):
    """Form for querying the database."""

    # select modalities to show
    modalities = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs=checkbox_attrs),
        choices=[(mod, mod) for mod in get_default_modalities()],
        initial=["CT", "MRI", "PET", "FNA", "diagnostic_consensus", "pathology", "pCT"],
    )
    modality_combine = forms.ChoiceField(
        widget=forms.Select(attrs={"onchange": "changeHandler();"}),
        choices=[
            ("max_llh", "maxLLH"),
            ("rank", "RANK"),
        ],
        label="Combine",
        initial="max_llh",
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

    datasets = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs=checkbox_attrs),
        choices=[],
        initial=[],
    )

    # tumor specific info
    subsites = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs=checkbox_attrs),
        choices=Subsites.all_choices(),
        initial=Subsites.all_values(),
    )

    t_stage = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs=checkbox_attrs),
        choices=TStages.choices,
        initial=TStages.values,
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
        """
        Extend default initialization to create lots of fields for the
        LNLs from a list and hide some datasets for unauthenticated users.
        """
        super().__init__(*args, **kwargs)

        # dynamically define which datasets should be selectable
        public_datasets = DataInterface().list_datasets_by(visibility="public")
        self.fields["datasets"].choices = format_dataset_choices(public_datasets)
        self.fields["datasets"].initial = public_datasets

        if user.is_authenticated:
            private_datasets = DataInterface().list_datasets_by(visibility="private")
            self.fields["datasets"].choices += format_dataset_choices(private_datasets)
            self.fields["datasets"].initial += private_datasets

        # add all LNL ToggleButtons so I don't have to write a myriad of them
        for side in ["ipsi", "contra"]:
            for lnl in LNLS:
                if lnl in ["I", "II", "V"]:
                    self.fields[f"{side}_{lnl}"] = ThreeWayToggle(
                        option_attrs={"onclick": "bothClickHandler(this)"}
                    )
                elif "a" in lnl or "b" in lnl:
                    self.fields[f"{side}_{lnl}"] = ThreeWayToggle(
                        option_attrs={"onclick": "subClickHandler(this)"}
                    )
                else:
                    self.fields[f"{side}_{lnl}"] = ThreeWayToggle()

    def clean(self):
        """
        Make sure LNLs I & II have correct values corresponding to their
        sublevels a & b. Also convert tstages from list of str to list of int.
        """
        cleaned_data = super().clean()

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

        self.logger.debug(f"cleaned data: {cleaned_data}")
        return cleaned_data

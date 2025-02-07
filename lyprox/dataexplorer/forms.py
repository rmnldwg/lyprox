"""
Defines the fields that can be used to query the patient records.

Basically, this defines what buttons, dropdowns, and checkboxes are displayed on the
dashboard and to some extent also how they look. Here, we also define the
`ThreeWayToggle` button that is used to select between three states: positive, negative,
and unknown. The `ThreeWayToggle` button is used for selecting HPV status, nicotine
abuse, LNL involvement and more.

Typically, when calling one of the `dataexplorer.views` functions, an instance of the
`DataexplorerForm` is created with the user's permissions and the initial data from the
`DataexplorerForm.from_initial` class method. This initial data is then used to display
the dashboard. Then, the user applies filters to the data and submits the form by
pressing the "Compute" button. The form is then validated and cleaned
(``form.is_valid()``), also in the `dataexplorer.views` module.

Note: the `DataexplorerForm` is not strictly used `as Django intends forms to be used`_.
In Django's logic, a form just after creation is "unbound" and in that state expects
user input (think of a login form with empty fields). However, in our dashboard, no
fields are ever "empty". Even when you first load the dashboard, the `ThreeWayToggle`
buttons are already set to a value (``None``). Therefore, we never have this "unbound"
state of the form. Instead, we always work with bound and validated forms, either
created from the initial defaults or from the user's input.

.. _as Django intends forms to be used: https://docs.djangoproject.com/en/4.2/ref/forms/
"""

import logging
from collections.abc import Generator
from typing import Any, TypeVar

from django import forms
from django.core.exceptions import ValidationError
from lydata.utils import get_default_modalities

from lyprox.dataexplorer.models import DatasetModel
from lyprox.dataexplorer.subsites import Subsites
from lyprox.loggers import FormLoggerMixin
from lyprox.settings import LNLS, TStages

logger = logging.getLogger(__name__)


def trio_to_bool(value: int | Any) -> bool | Any:
    """
    Transform -1, 0, and +1 to ``False``, ``None`` and ``True`` respectively.

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
    Widget that renders the three-way toggle button.

    It also allows to set the attributes of the individual inputs (radio buttons) as
    `option_attrs` as well as the attributes of the container as ``attrs``.
    """

    template_name = "widgets/three_way_toggle.html"
    """HTML template that renders the button containing its three options."""
    option_template_name = "widgets/three_way_toggle_option.html"
    """HTML template that renders the individual options of the button."""
    option_attrs = {"class": "radio is-hidden", "onchange": "changeHandler();"}
    """HTML attributes. Also adds the call to a JS function."""

    def __init__(
        self,
        attrs=None,
        choices=(),
        option_attrs=None,
        label=None,
        tooltip=None,
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
    Field to choose one of three options: ``True``, ``None`` and ``False``.

    ``True`` is represented by a plus sign and means "positive", ``None`` is
    represented by a ban sign and means "unknown", and ``False`` is represented by a
    minus sign and means "negative".

    The field is rendered by the `ThreeWayToggleWidget`. Every LNL's involvement as
    well as many binary risk factors such as smoking status, HPV status, and neck
    dissection status are represented by this field.
    """

    def __init__(
        self,
        attrs=None,
        option_attrs=None,
        label=None,
        tooltip=None,
        choices=None,
        initial=None,
        required=False,
        **kwargs,
    ):
        """Pass args like ``label`` and ``tooltip`` to constructor of custom widget."""
        if choices is None:
            choices = [(True, "plus"), (None, "ban"), (False, "minus")]

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

    def to_python(self, value: bool | None) -> bool | None:
        """Cast the string to an integer. ``""`` is interpreted as ``None``."""
        if value in [True, False, None]:
            return value

        if value == "":
            return None

        raise ValidationError(f"Invalid {value = } for ThreeWayToggle")


checkbox_attrs = {"class": "checkbox is-hidden", "onchange": "changeHandler();"}


class EasySubsiteChoiceField(forms.MultipleChoiceField):
    """Simple subclass that provides a convenience method to create subsite fields."""

    @classmethod
    def from_enum(cls, enum: type, **kwargs) -> "EasySubsiteChoiceField":
        """
        Create a field from a subsite enum.

        All this does is pass the ``enum``'s choices and values to the constructor as
        ``choices`` and ``initial``, respectively. It makes the field not required and
        uses a checkbox widget with the `checkbox_attrs` as ``attrs``.
        """
        default_kwargs = {
            "required": False,
            "widget": forms.CheckboxSelectMultiple(attrs=checkbox_attrs),
            "choices": enum.choices,
            "initial": enum.values,
        }
        default_kwargs.update(kwargs)
        return cls(**default_kwargs)


def get_modality_choices() -> list[tuple[str, str]]:
    """Return the choices for the modality field."""
    return [(mod, mod.replace("_", " ")) for mod in get_default_modalities()]


T = TypeVar("T", bound="DataexplorerForm")


class DataexplorerForm(FormLoggerMixin, forms.Form):
    """
    Form for querying the database.

    The form's fields somewhat mirror the fields in the `Statistics` class in
    the `query` module.
    """

    modalities = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs=checkbox_attrs),
        choices=get_modality_choices(),
        initial=["CT", "MRI", "PET", "FNA", "diagnostic_consensus", "pathology", "pCT"],
    )
    """Which modalities to combine into a consensus diagnosis."""

    modality_combine = forms.ChoiceField(
        widget=forms.Select(attrs={"onchange": "changeHandler();"}),
        choices=[
            ("max_llh", "maxLLH"),
            ("rank", "RANK"),
        ],
        label="Combine",
        initial="max_llh",
    )
    """Method to use to combine the modalities' LNL involvement diagnoses."""

    datasets = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs=checkbox_attrs),
        queryset=DatasetModel.objects.all().filter(is_private=False),
        initial=DatasetModel.objects.all().filter(is_private=False),
        required=False,
    )
    """Patients from which datasets to include in the query."""

    smoke = ThreeWayToggle(
        label="smoking status", tooltip="Select smokers or non-smokers"
    )
    """Select patients that are smokers, non-smokers, or unknown."""

    hpv = ThreeWayToggle(
        label="HPV status", tooltip="Select patients being HPV positive or negative"
    )
    """Select patients that are HPV positive, negative, or unknown."""

    surgery = ThreeWayToggle(
        label="neck dissection",
        tooltip="Include patients that have (or have not) received neck dissection",
    )
    """Did the patient undergo neck dissection?"""

    t_stage = EasySubsiteChoiceField.from_enum(TStages)
    """Only include patients with the selected T-stages."""

    is_n_plus = ThreeWayToggle(
        label="N+ vs N0", tooltip="Select all N+ (or N0) patients"
    )
    """Select patients with N+ or N0 status."""

    central = ThreeWayToggle(
        label="central", tooltip="Choose to in- or exclude patients with central tumors"
    )
    """Filter by whether the tumor is central or not."""

    midext = ThreeWayToggle(
        label="midline extension",
        tooltip=(
            "Investigate patients with tumors that do (or do not) "
            "cross the mid-sagittal plane"
        ),
    )
    """Filter by whether the tumor crosses the mid-sagittal plane."""

    show_percent = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.widgets.RadioSelect(
            attrs={"class": "radio is-hidden", "onchange": "changeHandler();"},
            choices=[(True, "percent"), (False, "absolute")],
        ),
    )
    """Show the statistics after querying as percentages or absolute numbers."""

    def __init__(self, *args, user, **kwargs):
        """
        Extend default initialization.

        After calling the parent constructor, the selectable datasets are populated
        based on the user's permissions. I.e., a logged-in user can see private
        datasets, while an anonymous user can only see public datasets.

        Then, the defined `Subsites` as separate `MultipleChoiceField` fields are added
        to the form. We do this dynamically via the `add_subsite_choice_fields` method,
        because we want to render the subsites separately in the frontend.

        Also, the LNL toggle buttons are added to the form dynamically, because it
        would be cumbersome to add them manually for each LNL and side.

        Note that the form contains the user input or initial values already upon
        initialization. But it is OK to add fields even after that, because the form
        only goes through its fields and tries to validate its data for each of then
        when ``form.is_valid()`` is called.
        """
        super().__init__(*args, **kwargs)
        self.update_dataset_options(user=user)
        self.add_subsite_choice_fields()
        self.add_lnl_toggle_buttons()

    def update_dataset_options(self, user) -> None:
        """Update the dataset choices based on the user's permissions."""
        if user.is_authenticated:
            self.fields["datasets"].queryset = DatasetModel.objects.all()
            self.fields["datasets"].initial = DatasetModel.objects.all()

    def add_subsite_choice_fields(self):
        """Add all subsite choice fields to the form."""
        for subsite, enum in Subsites.get_subsite_enums().items():
            self.fields[f"subsite_{subsite}"] = EasySubsiteChoiceField.from_enum(enum)

    def add_lnl_toggle_buttons(self) -> None:
        """Add all LNL toggle buttons to the form."""
        for side in ["ipsi", "contra"]:
            for lnl in LNLS:
                if lnl in ["I", "II", "V"]:
                    self.fields[f"{side}_{lnl}"] = ThreeWayToggle(
                        option_attrs={"onclick": "superClickHandler(this)"}
                    )
                elif "a" in lnl or "b" in lnl:
                    self.fields[f"{side}_{lnl}"] = ThreeWayToggle(
                        option_attrs={"onclick": "subClickHandler(this)"}
                    )
                else:
                    self.fields[f"{side}_{lnl}"] = ThreeWayToggle()

    @classmethod
    def from_initial(cls: type[T], user) -> T:
        """Return a bound form filled with the default values for each field."""
        form = cls(user=user)
        initial_data = {}
        for name, field in form.fields.items():
            initial_data[name] = form.get_initial_for_field(field, name)

        logger.info("Creating DataexplorerForm with initial data.")
        logger.debug(f"Initial data: {initial_data}")
        return cls(initial_data, user=user)

    def get_subsite_fields(self) -> list[str]:
        """Return the subsite checkboxes."""
        return [name for name in self.fields.keys() if name.startswith("subsite_")]

    @staticmethod
    def generate_icd_codes(cleaned_data: dict[str, Any]) -> Generator[str, None, None]:
        """Generate all subsite ICD codes."""
        for subsite in Subsites.get_subsite_enums().keys():
            yield from cleaned_data[f"subsite_{subsite}"]

    def check_lnl_conflicts(self, cleaned_data: dict[str, Any]) -> dict[str, Any]:
        """Ensure that LNLs I, II, and V are not in conflict with their sublevels."""
        for side in ["ipsi", "contra"]:
            for lnl in ["I", "II", "V"]:
                a = cleaned_data[f"{side}_{lnl}a"]
                b = cleaned_data[f"{side}_{lnl}b"]

                if a is True or b is True:
                    cleaned_data[f"{side}_{lnl}"] = True
                if a is False and b is False:
                    cleaned_data[f"{side}_{lnl}"] = False

        return cleaned_data

    def clean(self) -> dict[str, Any]:
        """
        Clean the form data.

        The default cleaning provided by Django is extended to deal with some special
        cases that arise from our data. On the one hand, this involved casting the
        ``t_stage`` list of values to integers, but more importantly, it also ensures
        that the sub- and superlevel involvement of the LNLs I, II, and V are not in
        conflict.
        """
        cleaned_data = super().clean()

        if len(self.errors) != 0:
            return {}

        cleaned_data["t_stage"] = [int(t) for t in cleaned_data["t_stage"]]
        cleaned_data["subsite"] = list(self.generate_icd_codes(cleaned_data))
        cleaned_data = self.check_lnl_conflicts(cleaned_data)

        self.logger.debug(f"cleaned data: {cleaned_data}")
        return cleaned_data

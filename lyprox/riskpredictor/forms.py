"""
This module contains the forms used in the riskpredictor app.

The first form, the `TrainedLymphModelForm`, is used to create a new
`models.TrainedLymphModel` and makes sure that the user enters a valid git repository
and revision.
"""
from typing import Any, Dict

from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.forms import ValidationError, widgets
from dvc.api import DVCFileSystem
from dvc.scm import CloneError, RevError
from lyscripts.predict.utils import complete_pattern

from .. import loggers
from ..dataexplorer.forms import ThreeWayToggle, trio_to_bool
from .models import TrainedLymphModel


class RangeInput(widgets.NumberInput):
    input_type = "range"


class TrainedLymphModelForm(loggers.FormLoggerMixin, forms.ModelForm):
    """Form for creating a new `TrainedLymphModel` instance."""
    class Meta:
        model = TrainedLymphModel
        fields = ["git_repo_url", "revision", "params_path", "num_samples"]
        widgets = {
            "git_repo_url": widgets.TextInput(attrs={
                "class": "input",
                "placeholder": "e.g. https://github.com/my/repo",
            }),
            "revision": widgets.TextInput(attrs={
                "class": "input",
                "placeholder": "e.g. `main` or a tag name",
            }),
            "params_path": widgets.TextInput(attrs={
                "class": "input",
                "placeholder": "e.g. `params.yaml`",
            }),
            "num_samples": widgets.NumberInput(attrs={
                "class": "input",
                "placeholder": "e.g. 1000",
            }),
        }

    def clean(self) -> Dict[str, Any]:
        """Check all the fields for validity."""
        git_repo_url = self.cleaned_data["git_repo_url"]
        revision = self.cleaned_data["revision"]
        params_path = self.cleaned_data["params_path"]

        try:
            fs = DVCFileSystem(url=git_repo_url, rev=revision)

            if not fs.isfile(params_path):
                self.add_error(
                    field="params_path",
                    error=ValidationError("Not a valid path to the model parameters."),
                )
        except CloneError as _e:
            self.add_error(
                field="git_repo_url",
                error=ValidationError("Not a valid git repository."),
            )
        except RevError as _e:
            self.add_error(
                field="revision",
                error=ValidationError("Not a valid git revision."),
            )


        return self.cleaned_data


class DashboardForm(forms.Form):
    """Form for the dashboard page."""
    is_submitted = forms.BooleanField(
        required=True, initial=True, widget=forms.HiddenInput
    )
    """Whether the form has been submitted via the button or not."""

    def __init__(self, *args, trained_lymph_model: TrainedLymphModel = None, **kwargs):
        super().__init__(*args, **kwargs)

        if trained_lymph_model is not None:
            self.trained_lymph_model = trained_lymph_model
            self.add_lnl_fields(self.trained_lymph_model)
            self.add_t_stage_field(self.trained_lymph_model)
            self.add_sens_spec_fields()

            if self.trained_lymph_model.is_midline:
                self.add_midline_field()


    def add_lnl_fields(self, trained_lymph_model: TrainedLymphModel):
        """Add the fields for the lymph node levels defined in the trained model."""
        for lnl in trained_lymph_model.lnls:
            self.fields[f"ipsi_{lnl}"] = ThreeWayToggle()

            if trained_lymph_model.is_bilateral:
                self.fields[f"contra_{lnl}"] = ThreeWayToggle()


    def add_t_stage_field(self, trained_lymph_model: TrainedLymphModel):
        """Add the field for the T stage with the choices being defined in the model."""
        self.fields["t_stage"] = forms.ChoiceField(
            choices=[(t, t) for t in trained_lymph_model.t_stages],
            initial=trained_lymph_model.t_stages[0],
        )


    def add_sens_spec_fields(self, step: float = 0.01):
        """Add the fields for the sensitivity and specificity."""
        self.fields["sensitivity"] = forms.FloatField(
            min_value=0.5, max_value=1, initial=0.8,
            widget=RangeInput(attrs={
                "class": "tag slider is-fullwidth",
                "min": "0.5",
                "max": "1",
                "step": f"{step:.2f}",
            }),
            validators=[
                MinValueValidator(0.5, "Sensitivity below 0.5 makes no sense"),
                MaxValueValidator(1, "Sensitivity above 1 makes no sense"),
            ],
        )
        self.fields["specificity"] = forms.FloatField(
            min_value=0.5, max_value=1, initial=0.8,
            widget=RangeInput(attrs={
                "class": "tag slider is-fullwidth",
                "min": "0.5",
                "max": "1",
                "step": f"{step:.2f}",
            }),
            validators=[
                MinValueValidator(0.5, "Specificty below 0.5 makes no sense"),
                MaxValueValidator(1, "Specificty above 1 makes no sense"),
            ]
        )


    def add_midline_field(self):
        """Add the field for the midline status."""
        self.fields["midline_extension"] = ThreeWayToggle(
            label=None,
            tooltip="Does the tumor cross the mid-sagittal line?",
            initial=-1,
        )


    def clean_midline_extension(self) -> bool:
        """For now, the midline extension cannot be unknown (value of 0)."""
        midline_extension = self.cleaned_data["midline_extension"]
        if midline_extension == 0:
            raise ValidationError("Midline extension cannot be unknown.")
        return midline_extension


    def clean(self) -> Dict[str, Any]:
        """Transform three-way toggles to booleans."""
        cleaned_data = super().clean()

        for field_name, field_value in cleaned_data.items():
            cleaned_data[field_name] = trio_to_bool(field_value)

        diagnosis = {}
        for side in ["ipsi", "contra"]:
            diagnosis[side] = {}
            for lnl in self.trained_lymph_model.lnls:
                if (key := f"{side}_{lnl}") not in cleaned_data:
                    continue
                diagnosis[side][lnl] = cleaned_data.pop(key)

        cleaned_data["diagnosis"] = complete_pattern(
            diagnosis, self.trained_lymph_model.lnls
        )
        return cleaned_data

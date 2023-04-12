"""
This module contains the forms used in the riskpredictor app.

The first form, the `TrainedLymphModelForm`, is used to create a new
`models.TrainedLymphModel` and makes sure that the user enters a valid git repository
and revision.
"""
from typing import Any, Dict

from django import forms
from django.forms import ValidationError, widgets
from dvc.api import DVCFileSystem
from dvc.scm import CloneError, RevError

from .. import loggers
from ..dataexplorer.forms import ThreeWayToggle
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
        except CloneError as e:
            self.add_error(
                field="git_repo_url",
                error=ValidationError("Not a valid git repository."),
            )
        except RevError as e:
            self.add_error(
                field="revision",
                error=ValidationError("Not a valid git revision."),
            )


        return self.cleaned_data


class DashboardForm(forms.Form):
    """Form for the dashboard page."""
    def __init__(self, *args, trained_lymph_model: TrainedLymphModel = None, **kwargs):
        super().__init__(*args, **kwargs)

        if trained_lymph_model is not None:
            self.add_lnl_fields(trained_lymph_model)
            self.add_t_stage_field(trained_lymph_model)
            self.add_sens_spec_fields()

            if trained_lymph_model.is_midline or True:
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
            min_value=0, max_value=1, initial=0.8,
            widget=RangeInput(attrs={
                "class": "tag slider is-fullwidth",
                "min": "0.5",
                "max": "1",
                "step": f"{step:.2f}",
            }),
        )
        self.fields["specificity"] = forms.FloatField(
            min_value=0, max_value=1, initial=0.8,
            widget=RangeInput(attrs={
                "class": "tag slider is-fullwidth",
                "min": "0.5",
                "max": "1",
                "step": f"{step:.2f}",
            }),
        )

    def add_midline_field(self):
        """Add the field for the midline status."""
        self.fields["midline_extension"] = ThreeWayToggle(
            label=None,
            tooltip="Does the tumor cross the mid-sagittal line?",
        )

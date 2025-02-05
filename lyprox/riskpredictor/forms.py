"""
Forms used in the `riskpredictor` app.

The first form, the `InferenceResultForm`, is used to create a new
`models.InferenceResult` and makes sure that the user enters a valid git repository
and revision.
"""

from typing import Any

from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.forms import ValidationError, widgets
from dvc.api import DVCFileSystem
from dvc.scm import CloneError, RevError
from lymph import models

from lyprox import loggers
from lyprox.dataexplorer.forms import ThreeWayToggle
from lyprox.riskpredictor.models import InferenceResult


class RangeInput(widgets.NumberInput):
    """A widget for a range slider input field."""

    input_type = "range"


class InferenceResultForm(loggers.FormLoggerMixin, forms.ModelForm):
    """Form for creating a new `InferenceResult` instance."""

    class Meta:
        """Meta class for the form."""

        model = InferenceResult
        fields = [
            "repo_name",
            "ref",
            "graph_config_path",
            "model_config_path",
            "dist_configs_path",
            "num_samples",
        ]
        widgets = {
            "ref": widgets.TextInput(
                attrs={
                    "class": "input",
                    "placeholder": "e.g. `main`, commit hash, or tag name",
                }
            ),
            "graph_config_path": widgets.TextInput(
                attrs={
                    "class": "input",
                    "placeholder": "e.g. `graph.ly.yaml`",
                }
            ),
            "model_config_path": widgets.TextInput(
                attrs={
                    "class": "input",
                    "placeholder": "e.g. `model.ly.yaml`",
                }
            ),
            "dist_configs_path": widgets.TextInput(
                attrs={
                    "class": "input",
                    "placeholder": "e.g. `graph.ly.yaml`",
                }
            ),
            "num_samples": widgets.NumberInput(
                attrs={
                    "class": "input",
                    "placeholder": "e.g. 100",
                }
            ),
        }

    def clean(self) -> dict[str, Any]:
        """Check all the fields for validity."""
        cleaned_data = super().clean()
        repo_name = cleaned_data["repo_name"]
        repo_url = f"https://github.com/{repo_name}"
        ref = cleaned_data["ref"]
        graph_config_path = cleaned_data["graph_config_path"]
        model_config_path = cleaned_data["model_config_path"]
        distributions_config_path = cleaned_data["distributions_config_path"]

        try:
            fs = DVCFileSystem(url=repo_url, rev=ref)

            if not fs.isfile(graph_config_path):
                self.add_error(
                    field="graph_config_path",
                    error=ValidationError("Not a valid path to the graph config."),
                )
            if not fs.isfile(model_config_path):
                self.add_error(
                    field="model_config_path",
                    error=ValidationError("Not a valid path to the model config."),
                )
            if not fs.isfile(distributions_config_path):
                self.add_error(
                    field="distributions_config_path",
                    error=ValidationError("Not a valid path to the distributions."),
                )
        except CloneError as _e:
            self.add_error(
                field="repo_name",
                error=ValidationError("Not an existing GitHub repository."),
            )
        except RevError as _e:
            self.add_error(
                field="ref",
                error=ValidationError("Not a valid git ref."),
            )

        return cleaned_data


class DashboardForm(forms.Form):
    """Form for the dashboard page."""

    is_submitted = forms.BooleanField(
        required=True, initial=True, widget=forms.HiddenInput
    )
    """Whether the form has been submitted via the button or not."""

    def __init__(self, *args, inference_result: InferenceResult = None, **kwargs):
        """Initialize the form and add the fields for the lymph node levels."""
        super().__init__(*args, **kwargs)

        if inference_result is not None:
            self.inference_result = inference_result
            self.model = self.inference_result.construct_model()
            self.add_lnl_fields()
            self.add_t_stage_field()
            self.add_sens_spec_fields()

            if isinstance(self.model, models.Midline):
                self.add_midline_field()

    def get_lnls(self):
        """Get the lymph node levels from the model."""
        if isinstance(self.model, models.Unilateral):
            return self.model.graph.lnls
        if isinstance(self.model, models.Bilateral):
            return self.model.ipsi.graph.lnls
        if isinstance(self.model, models.Midline):
            return self.model.ext.ipsi.graph.lnls

        raise RuntimeError(f"Model type {type(self.model)} not recognized.")

    def add_lnl_fields(self):
        """Add the fields for the lymph node levels defined in the trained model."""
        lnls = self.get_lnls()

        for lnl in lnls:
            self.fields[f"ipsi_{lnl}"] = ThreeWayToggle(initial=-1)

            if isinstance(self.model, models.Bilateral | models.Midline):
                self.fields[f"contra_{lnl}"] = ThreeWayToggle(initial=-1)

    def add_t_stage_field(self):
        """Add the field for the T stage with the choices being defined in the model."""
        t_stages = list(self.model.get_all_distributions())
        self.fields["t_stage"] = forms.ChoiceField(
            choices=t_stages,
            initial=t_stages[0],
        )

    def add_sens_spec_fields(self, step: float = 0.01):
        """Add the fields for the sensitivity and specificity."""
        self.fields["sensitivity"] = forms.FloatField(
            min_value=0.5,
            max_value=1,
            initial=0.8,
            widget=RangeInput(
                attrs={
                    "class": "tag slider is-fullwidth",
                    "min": "0.5",
                    "max": "1",
                    "step": f"{step:.2f}",
                }
            ),
            validators=[
                MinValueValidator(0.5, "Sensitivity below 0.5 makes no sense"),
                MaxValueValidator(1, "Sensitivity above 1 makes no sense"),
            ],
        )
        self.fields["specificity"] = forms.FloatField(
            min_value=0.5,
            max_value=1,
            initial=0.8,
            widget=RangeInput(
                attrs={
                    "class": "tag slider is-fullwidth",
                    "min": "0.5",
                    "max": "1",
                    "step": f"{step:.2f}",
                }
            ),
            validators=[
                MinValueValidator(0.5, "Specificty below 0.5 makes no sense"),
                MaxValueValidator(1, "Specificty above 1 makes no sense"),
            ],
        )

    def add_midline_field(self):
        """Add the field for the midline status."""
        self.fields["midline_extension"] = ThreeWayToggle(
            label=None,
            tooltip="Does the tumor cross the mid-sagittal line?",
            choices=[(True, "plus"), (None, "ban"), (False, "minus")],
            initial=False,
        )

    def clean_midline_extension(self) -> bool:
        """For now, the midline extension cannot be unknown (value of 0)."""
        midline_extension = self.cleaned_data["midline_extension"]
        if midline_extension is None:
            raise ValidationError("Midline extension cannot be unknown.")
        return midline_extension

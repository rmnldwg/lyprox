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
from .models import TrainedLymphModel


class TrainedLymphModelForm(loggers.FormLoggerMixin, forms.ModelForm):
    """Form for creating a new `TrainedLymphModel` instance."""
    class Meta:
        model = TrainedLymphModel
        fields = ["git_repo_url", "revision", "samples_path", "params_path", "num_samples"]
        widgets = {
            "git_repo_url": widgets.TextInput(attrs={
                "class": "input",
                "placeholder": "e.g. https://github.com/my/repo",
            }),
            "revision": widgets.TextInput(attrs={
                "class": "input",
                "placeholder": "e.g. `main` or a tag name",
            }),
            "samples_path": widgets.TextInput(attrs={
                "class": "input",
                "placeholder": "e.g. `models/samples.hdf5`",
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
        samples_path = self.cleaned_data["samples_path"]
        params_path = self.cleaned_data["params_path"]

        try:
            fs = DVCFileSystem(url=git_repo_url, rev=revision)
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

        if not fs.isfile(samples_path):
            self.add_error(
                field="samples_path",
                error=ValidationError("Not a valid path to the parameter samples."),
            )

        if not fs.isfile(params_path):
            self.add_error(
                field="params_path",
                error=ValidationError("Not a valid path to the model parameters."),
            )

        return self.cleaned_data

"""
Module for the views of the riskpredictor app.
"""
# pylint: disable=attribute-defined-outside-init
from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, ListView

from ..loggers import ViewLoggerMixin
from . import predict
from .forms import DashboardForm, TrainedLymphModelForm
from .models import TrainedLymphModel


class AddTrainedLymphModelView(
    ViewLoggerMixin,
    LoginRequiredMixin,
    CreateView,
):
    """View for adding a new `TrainedLymphModel` instance."""
    model = TrainedLymphModel
    form_class = TrainedLymphModelForm
    template_name = "riskpredictor/trainedlymphmodel_form.html"
    success_url = "/riskpredictor/list/"


class ChooseTrainedLymphModelView(
    ViewLoggerMixin,
    ListView,
):
    """View for choosing a `TrainedLymphModel` instance."""
    model = TrainedLymphModel
    template_name = "riskpredictor/trainedlymphmodel_list.html"
    context_object_name = "trained_lymph_models"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        self.logger.info(context)
        return context


class RiskPredictionView(
    ViewLoggerMixin,
    DetailView,
):
    """View for the dashboard of the riskpredictor app."""
    model = TrainedLymphModel
    form_class = DashboardForm
    template_name = "riskpredictor/dashboard.html"
    context_object_name = "trained_lymph_model"


    def handle_form(
        self,
        trained_lymph_model: TrainedLymphModel,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Populate the form and compute the risks.

        Either fill the form with the request data or with the initial data. Then, call
        the risk prediction methods and store the results in the `risks` attribute.
        """
        self.form = self.form_class(data, trained_lymph_model=trained_lymph_model)

        if not self.form.is_valid():
            if self.form.cleaned_data.get("is_submitted", False):
                errors = self.form.errors.as_data()
                self.logger.warning("Form is not valid, errors are: %s", errors)
                self.risks = predict.default_risks(trained_lymph_model)
                return

            self.initialize_form(trained_lymph_model)

        self.risks = predict.risks(
            trained_lymph_model=trained_lymph_model,
            **self.form.cleaned_data,
        )


    def initialize_form(self, trained_lymph_model):
        """Fill the form with the initial data from the respective form fields."""
        initial = {}
        for field_name, field in self.form.fields.items():
            initial[field_name] = self.form.get_initial_for_field(field, field_name)

        self.form = self.form_class(initial, trained_lymph_model=trained_lymph_model)

        if not self.form.is_valid():
            errors = self.form.errors.as_data()
            self.logger.warning("Initial form still invalid, errors are: %s", errors)


    def get_object(self, queryset=None) -> TrainedLymphModel:
        trained_lymph_model = super().get_object(queryset)
        self.handle_form(trained_lymph_model, data=self.request.GET)
        return trained_lymph_model


    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        context["risks"] = self.risks
        return context

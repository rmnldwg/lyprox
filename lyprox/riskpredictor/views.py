"""
Module for the views of the riskpredictor app.
"""
from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, ListView

from ..loggers import ViewLoggerMixin
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

    def compute_risk(
        self,
        trained_lymph_model: TrainedLymphModel,
        data: Dict[str, Any],
    ):
        """Compute the risk for a given request."""
        self.form = self.form_class(data, trained_lymph_model=trained_lymph_model)

        if not self.form.is_valid():
            initial_data = {}
            for field_name, field in self.form.fields.items():
                initial_data[field_name] = self.form.get_initial_for_field(
                    field, field_name
                )
            self.form = self.form_class(initial_data, trained_lymph_model=trained_lymph_model)


    def get_object(self, queryset=None) -> TrainedLymphModel:
        trained_lymph_model = super().get_object(queryset)
        self.risks = self.compute_risk(trained_lymph_model, data=self.request.GET)
        return trained_lymph_model

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        context["risks"] = self.risks
        return context

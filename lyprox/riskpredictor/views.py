"""
Module for the views of the riskpredictor app.
"""
# pylint: disable=attribute-defined-outside-init
from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, ListView

from ..loggers import ViewLoggerMixin
from . import predict
from .forms import DashboardForm, InferenceResultForm
from .models import InferenceResult


class AddInferenceResultView(
    ViewLoggerMixin,
    LoginRequiredMixin,
    CreateView,
):
    """View for adding a new `InferenceResult` instance."""
    model = InferenceResult
    form_class = InferenceResultForm
    template_name = "riskpredictor/trainedlymphmodel_form.html"
    success_url = "/riskpredictor/list/"


class ChooseInferenceResultView(
    ViewLoggerMixin,
    ListView,
):
    """View for choosing a `InferenceResult` instance."""
    model = InferenceResult
    template_name = "riskpredictor/trainedlymphmodel_list.html"
    context_object_name = "inference_results"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        self.logger.info(context)
        return context


class RiskPredictionView(
    ViewLoggerMixin,
    DetailView,
):
    """View for the dashboard of the riskpredictor app."""
    model = InferenceResult
    form_class = DashboardForm
    template_name = "riskpredictor/dashboard.html"
    context_object_name = "inference_result"


    def handle_form(
        self,
        inference_result: InferenceResult,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Populate the form and compute the risks.

        Either fill the form with the request data or with the initial data. Then, call
        the risk prediction methods and store the results in the `risks` attribute.
        """
        self.form = self.form_class(data, inference_result=inference_result)

        if not self.form.is_valid():
            if self.form.cleaned_data.get("is_submitted", False):
                errors = self.form.errors.as_data()
                self.logger.warning("Form is not valid, errors are: %s", errors)
                self.risks = predict.default_risks(inference_result)
                return

            self.initialize_form(inference_result)

        self.risks = predict.risks(
            inference_result=inference_result,
            **self.form.cleaned_data,
        )


    def initialize_form(self, inference_result):
        """Fill the form with the initial data from the respective form fields."""
        initial = {}
        for field_name, field in self.form.fields.items():
            initial[field_name] = self.form.get_initial_for_field(field, field_name)

        self.form = self.form_class(initial, inference_result=inference_result)

        if not self.form.is_valid():
            errors = self.form.errors.as_data()
            self.logger.warning("Initial form still invalid, errors are: %s", errors)


    def get_object(self, queryset=None) -> InferenceResult:
        inference_result = super().get_object(queryset)
        self.handle_form(inference_result, data=self.request.GET)
        return inference_result


    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        context["risks"] = self.risks
        return context

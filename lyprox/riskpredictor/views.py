"""
Module for the views of the riskpredictor app.
"""
# pylint: disable=attribute-defined-outside-init
import json
import logging
from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import CreateView, DetailView, ListView

from ..loggers import ViewLoggerMixin
from . import predict
from .forms import DashboardForm, InferenceResultForm
from .models import InferenceResult

logger = logging.getLogger(__name__)


def test_view(request):
    """View for testing the riskpredictor app."""
    return render(request, "riskpredictor/test.html")


class AddInferenceResultView(
    ViewLoggerMixin,
    LoginRequiredMixin,
    CreateView,
):
    """View for adding a new `InferenceResult` instance."""
    model = InferenceResult
    form_class = InferenceResultForm
    template_name = "riskpredictor/inference_result_form.html"
    success_url = "/riskpredictor/list/"


class ChooseInferenceResultView(
    ViewLoggerMixin,
    ListView,
):
    """View for choosing a `InferenceResult` instance."""
    model = InferenceResult
    template_name = "riskpredictor/inference_result_list.html"
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


    @classmethod
    def handle_form(
        cls,
        inference_result: InferenceResult,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Populate the form and compute the risks.

        Either fill the form with the request data or with the initial data. Then, call
        the risk prediction methods and store the results in the `risks` attribute.
        """
        form = cls.form_class(data, inference_result=inference_result)

        if not form.is_valid():
            logger.info(form.errors.as_data())
            if form.cleaned_data.get("is_submitted", False):
                errors = form.errors.as_data()
                logger.warning("Form is not valid, errors are: %s", errors)
                risks = predict.default_risks(inference_result)
                return form, risks

            form = cls.initialize_form(form, inference_result)

        risks = predict.risks(
            inference_result=inference_result,
            **form.cleaned_data,
        )

        return form, risks


    @classmethod
    def initialize_form(
        cls,
        form: DashboardForm,
        inference_result: InferenceResult,
    ) -> DashboardForm:
        """Fill the form with the initial data from the respective form fields."""
        initial = {}
        for field_name, field in form.fields.items():
            initial[field_name] = form.get_initial_for_field(field, field_name)

        form = cls.form_class(initial, inference_result=inference_result)

        if not form.is_valid():
            errors = form.errors.as_data()
            logger.warning("Initial form still invalid, errors are: %s", errors)

        return form


    def get_object(self, queryset=None) -> InferenceResult:
        inference_result = super().get_object(queryset)
        form, risks = self.handle_form(inference_result, data=self.request.GET)
        self.form = form
        self.risks = risks
        return inference_result


    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        context["risks"] = self.risks
        return context


def riskpredictor_AJAX_view(request, pk: int, **kwargs: Any) -> JsonResponse:
    """View for the AJAX request of the riskpredictor dashboard.

    This view receives the same data as the `RiskPredictionView`, albeit in JSON format.
    It then computes the risks and returns them in JSON format again to be handled
    by JavaScript on the client side.
    """
    data = json.loads(request.body.decode("utf-8"))
    inference_result = InferenceResult.objects.get(pk=pk)
    form, risks = RiskPredictionView.handle_form(inference_result, data)
    risks["type"] = "risks"   # tells JavaScript how to write the labels
    risks["total"] = 100.     # necessary for JavaScript barplot updater

    if form.is_valid():
        logger.info("AJAX form valid, returning success and risks.")
        return JsonResponse(data=risks)

    logger.warning("AJAX form invalid.")
    return JsonResponse(data={"error": "Something went wrong."}, status=400)


def help_view(request) -> HttpResponse:
    """View for the help page of the riskpredictor app."""
    template_name = "riskpredictor/help/index.html"
    context = {}
    return render(request, template_name, context)

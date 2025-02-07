"""Module for the views of the riskpredictor app."""

# pylint: disable=attribute-defined-outside-init
import json
import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import CreateView, ListView

from ..loggers import ViewLoggerMixin
from .forms import CheckpointModelForm, RiskpredictorForm
from .models import CheckpointModel

logger = logging.getLogger(__name__)


def test_view(request):
    """View for testing the riskpredictor app."""
    return render(request, "riskpredictor/test.html")


class AddCheckpointModelView(
    ViewLoggerMixin,
    LoginRequiredMixin,
    CreateView,
):
    """View for adding a new `CheckpointModel` instance."""

    model = CheckpointModel
    form_class = CheckpointModelForm
    template_name = "riskpredictor/inference_result_form.html"
    success_url = "/riskpredictor/list/"


class ChooseCheckpointModelView(
    ViewLoggerMixin,
    ListView,
):
    """View for choosing a `CheckpointModel` instance."""

    model = CheckpointModel
    template_name = "riskpredictor/inference_result_list.html"
    context_object_name = "inference_results"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the form to the context."""
        context = super().get_context_data(**kwargs)
        self.logger.info(context)
        return context


def riskpredictor_view(request, checkpoint_pk: int) -> HttpResponse:
    """View for the riskpredictor dashboard."""
    request_data = request.GET
    checkpoint = CheckpointModel.objects.get(pk=checkpoint_pk)
    form = RiskpredictorForm(request_data, checkpoint=checkpoint)

    if not form.is_valid():
        logger.info("Riskpredictor form not valid.")
        form = RiskpredictorForm.from_initial(checkpoint=checkpoint)

    if not form.is_valid():
        logger.error("Form is not valid even after initializing with initial data.")
        return HttpResponse("Form is not valid.")

    risks = ...

    context = {
        "form": form,
        "risks": risks,
    }
    return render(request, "riskpredictor/dashboard.html", context)


def riskpredictor_ajax_view(request, pk: int, **kwargs: Any) -> JsonResponse:
    """
    View for the AJAX request of the riskpredictor dashboard.

    This view receives the same data as the `RiskPredictionView`, albeit in JSON format.
    It then computes the risks and returns them in JSON format again to be handled
    by JavaScript on the client side.
    """
    _data = json.loads(request.body.decode("utf-8"))
    _inference_result = CheckpointModel.objects.get(pk=pk)
    form, risks = ...
    risks["type"] = "risks"  # tells JavaScript how to write the labels
    risks["total"] = 100.0  # necessary for JavaScript barplot updater

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

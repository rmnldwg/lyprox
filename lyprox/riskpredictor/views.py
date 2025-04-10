"""Module for the views of the riskpredictor app."""

# pylint: disable=attribute-defined-outside-init
import json
import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import CreateView, ListView

from lyprox.loggers import ViewLoggerMixin
from lyprox.riskpredictor import predict
from lyprox.riskpredictor.forms import CheckpointModelForm, RiskpredictorForm
from lyprox.riskpredictor.models import CheckpointModel

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
    template_name = "riskpredictor/checkpoint_form.html"
    success_url = "/riskpredictor/list/"


class ChooseCheckpointModelView(ViewLoggerMixin, ListView):
    """View for choosing a `CheckpointModel` instance."""

    model = CheckpointModel
    template_name = "riskpredictor/checkpoint_list.html"
    context_object_name = "checkpoints"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the form to the context."""
        context = super().get_context_data(**kwargs)
        self.logger.info(context)
        return context


def render_risk_prediction(request: HttpRequest, checkpoint_pk: int) -> HttpResponse:
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

    lnls = list(form.get_lnls())
    risks = predict.compute_risks(
        checkpoint=checkpoint,
        form_data=form.cleaned_data,
        lnls=lnls,
    )
    graph_config, model_config, dist_configs, _version = checkpoint.validate_configs()
    context = {
        "checkpoint": checkpoint,
        "form": form,
        "risks": risks,
        "lnls": lnls,
        "graph_params": graph_config.model_dump(),
        "model_params": model_config.model_dump(),
        "dist_params": {
            dist: dist_config.model_dump() for dist, dist_config in dist_configs.items()
        },
    }
    return render(request, "riskpredictor/layout.html", context)


def update_risk_prediction(request: HttpRequest, checkpoint_pk: int) -> JsonResponse:
    """View for the AJAX request of the riskpredictor dashboard.

    This view receives the same data as the `render_risk_prediction` function, but in
    JSON format. It then computes the risks and returns them in JSON format again to be
    handled by JavaScript on the client side.
    """
    request_data = json.loads(request.body.decode("utf-8"))
    checkpoint = CheckpointModel.objects.get(pk=checkpoint_pk)
    form = RiskpredictorForm(request_data, checkpoint=checkpoint)

    if not form.is_valid():
        logger.error("Riskpredictor from from AJAX request not valid.")
        return JsonResponse({"error": "Form is not valid."})

    lnls = list(form.get_lnls())
    risks = predict.compute_risks(
        checkpoint=checkpoint,
        form_data=form.cleaned_data,
        lnls=lnls,
    )
    risks = risks.model_dump()
    risks["total"] = 100.0
    risks["type"] = "risk"
    return JsonResponse(risks)


def help_view(request) -> HttpResponse:
    """View for the help page of the riskpredictor app."""
    template_name = "riskpredictor/help/index.html"
    context = {}
    return render(request, template_name, context)

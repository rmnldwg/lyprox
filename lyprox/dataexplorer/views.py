"""
The `views` module in the `dataexplorer` app mostly handles the
`DashboardView`, which takes care of initializing the complex
`forms.DashboardForm`, passing the cleaned values to all the filtering
functions in the `query` module to finally pass the queried information to
the context variable that is rendered into the HTML response.
"""

import json
import logging
from typing import Any

import numpy as np
from django.http import HttpResponseBadRequest
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
from lydata.utils import get_default_modalities

from lyprox.dataexplorer.forms import DashboardForm
from lyprox.dataexplorer.loader import DataInterface
from lyprox.dataexplorer.query import Statistics, execute_query
from lyprox.settings import LNLS

logger = logging.getLogger(__name__)


def help_view(request) -> HttpResponse:
    """Simply display the dashboard help text."""
    template_name = "dataexplorer/help/index.html"
    context = {"modalities": get_default_modalities()}
    return render(request, template_name, context)


def transform_np_to_lists(stats: dict[str, Any]) -> dict[str, Any]:
    """
    If ``stats`` contains any values that are of type ``np.ndarray``, then they are
    converted to normal lists.
    """
    for key, value in stats.items():
        if isinstance(value, np.ndarray):
            stats[key] = value.tolist()

    return stats


def dashboard_view(request):
    """Return the dashboard view when the user first accesses the dashboard."""
    request_data = request.GET
    form = DashboardForm(request_data, user=request.user)

    if not form.is_valid():
        logger.info("Dashboard form not valid.")
        form = DashboardForm.from_initial(user=request.user)

    if not form.is_valid():
        logger.error("Form is not valid even after initializing with initial data.")
        return HttpResponseBadRequest("Form is not valid.")

    patients = execute_query(cleaned_form=form.cleaned_data)

    context = {
        "form": form,
        "modalities": get_default_modalities(),
        "stats": Statistics.from_dataset(patients),
    }

    return render(request, "dataexplorer/layout.html", context)


def dashboard_ajax_view(request):
    """
    View that receives JSON data from the AJAX request and cleans it using the
    same method as the class-based ``DashboardView``.
    """
    request_data = json.loads(request.body.decode("utf-8"))
    form = DashboardForm(request_data, user=request.user)

    if not form.is_valid():
        logger.error("Form is not valid even after initializing with initial data.")
        return JsonResponse(data={"error": "Something went wrong."}, status=400)

    patients = execute_query(cleaned_form=form.cleaned_data)
    stats = Statistics.from_dataset(patients).model_dump()
    stats["type"] = "stats"
    return JsonResponse(data=stats)

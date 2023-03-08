"""
The `views` module in the `dashboard` app mostly handles the
`DashboardView`, which takes care of initializing the complex
`forms.DashboardForm`, passing the cleaned values to all the filtering
functions in the `query` module to finally pass the queried information to
the context variable that is rendered into the HTML response.
"""

import json
import logging
from typing import Any, Dict

import numpy as np
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import generic

from core.loggers import ViewLoggerMixin
from patients.models import Diagnose, Patient

from . import query

from.forms import DashboardForm

logger = logging.getLogger(__name__)


def help_view(request) -> HttpResponse:
    """Simply display the dashboard help text."""
    template_name = "dashboard/help/index.html"
    context = {"modalities": list(Diagnose.Modalities)}
    return render(request, template_name, context)


class DashboardView(ViewLoggerMixin, generic.ListView):
    """
    Use the `forms.DashboardForm` and the `patients.models.Patient` model
    along with the `query` functions to extract the requested information
    from the database and render it into the HTML response displaying the
    lymphatic patterns of progression.
    """
    model = Patient
    form_class = DashboardForm
    template_name = "dashboard/layout.html"
    action = "display_dashboard_stats"

    @classmethod
    def _get_queryset(cls, data, user, logger):
        form = cls.form_class(data, user=user)
        patients = Patient.objects.all()

        if not form.is_valid():
            # fill form with initial values from respective form fields when
            # validation fails
            initial_data = {}
            for field_name, field in form.fields.items():
                initial_data[field_name] = form.get_initial_for_field(
                    field, field_name
                )
            form = cls.form_class(initial_data, user=user)

            if not form.is_valid():
                # return empy queryset when something goes wrong with the validation of
                # the inital queryset
                logger.warn(
                    "Initial form is invalid, errors are: "
                    f"{form.errors.as_data()}"
                )
                patients = Patient.objects.none()

        patients, statistics = query.run_query(patients, form.cleaned_data)

        return form, patients, statistics

    def get_queryset(self):
        data = self.request.GET
        user = self.request.user
        form, queryset, stats = self._get_queryset(data, user, self.logger)
        self.form = form
        self.stats = stats
        return queryset

    def get_context_data(self) -> Dict[str, Any]:
        """
        Pass form and stats to the context. No need to have the list of patients in
        there too.
        """
        context = {
            "form": self.form,
            "stats": self.stats,
            "modalities": list(Diagnose.Modalities),
        }

        if self.form.is_valid():
            context["show_percent"] = self.form.cleaned_data["show_percent"]

        return context


def transform_np_to_lists(stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    If ``stats`` contains any values that are of type ``np.ndarray``, then they are
    converted to normal lists.
    """
    for key, value in stats.items():
        if isinstance(value, np.ndarray):
            stats[key] = value.tolist()

    return stats


def dashboard_AJAX_view(request):
    """
    View that receives JSON data from the AJAX request and cleans it using the
    same method as the class-based ``DashboardView``.
    """
    data = json.loads(request.body.decode("utf-8"))
    user = request.user
    form, _, stats = DashboardView._get_queryset(data, user, logger)
    stats = transform_np_to_lists(stats)

    if form.is_valid():
        logger.info("AJAX form valid, returning success and stats.")
        return JsonResponse(data=stats)

    return JsonResponse(
        data={"error": "Something went wrong."},
        status=400,
    )

"""
The `views` module in the `dashboard` app mostly handles the
`DashboardView`, which takes care of initializing the complex
`forms.DashboardForm`, passing the cleaned values to all the filtering
functions in the `query` module to finally pass the queried information to
the context variable that is rendered into the HTML response.
"""

import time
from typing import Any, Dict
import json
import logging

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
        queryset = Patient.objects.all()
        start_querying = time.perf_counter()

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
            queryset = Patient.objects.none()

        # perform the actual querying
        queryset = query.patient_specific(
            patient_queryset=queryset, **form.cleaned_data
        )
        queryset = query.tumor_specific(
            patient_queryset=queryset, **form.cleaned_data
        )
        queryset, combined_involvement = query.diagnose_specific(
            patient_queryset=queryset, **form.cleaned_data
        )
        queryset, combined_involvement = query.n_zero_specific(
            patient_queryset=queryset,
            combined_involvement=combined_involvement,
            n_status=form.cleaned_data['n_status']
        )
        queryset, stats = query.count_patients(
            patient_queryset=queryset,
            combined_involvement=combined_involvement
        )

        end_querying = time.perf_counter()
        logger.info(
            f'Querying finished in {end_querying - start_querying:.3f} seconds'
        )
        return form, queryset, stats

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


def dashboard_AJAX_view(request):
    """
    View that receives JSON data from the AJAX request and cleans it using the
    same method as the class-based ``DashboardView``.
    """
    data = json.loads(request.body.decode("utf-8"))
    user = request.user
    form, queryset, stats = DashboardView._get_queryset(data, user, logger)

    if form.is_valid():
        logger.info("AJAX form valid, returning success and stats.")
        return JsonResponse(
            data={"success": True, "queryset": queryset, "stats": stats}
        )

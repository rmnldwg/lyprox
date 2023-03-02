"""
The `views` module in the `dashboard` app mostly handles the
`DashboardView`, which takes care of initializing the complex
`forms.DashboardForm`, passing the cleaned values to all the filtering
functions in the `query` module to finally pass the queried information to
the context variable that is rendered into the HTML response.
"""

import time
from typing import Any, Dict

from django.http.response import HttpResponse
from django.shortcuts import render
from django.views import generic

from core.loggers import ViewLoggerMixin
from patients.models import Diagnose, Patient

from . import query

from.forms import DashboardForm


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

    def get_queryset(self):
        self.form = self.form_class(self.request.GET or None,
                                    user=self.request.user)
        queryset = Patient.objects.all()
        start_querying = time.perf_counter()

        if self.request.method == "GET" and self.form.is_valid():
            queryset = query.patient_specific(
                patient_queryset=queryset, **self.form.cleaned_data
            )
            queryset = query.tumor_specific(
                patient_queryset=queryset, **self.form.cleaned_data
            )
            queryset, combined_involvement = query.diagnose_specific(
                patient_queryset=queryset, **self.form.cleaned_data
            )
            queryset, combined_involvement = query.n_zero_specific(
                patient_queryset=queryset,
                combined_involvement=combined_involvement,
                n_status=self.form.cleaned_data['n_status']
            )
            queryset, counts = query.count_patients(
                patient_queryset=queryset,
                combined_involvement=combined_involvement
            )
            self.stats = counts

        else:
            # fill form with initial values from respective form fields
            initial_data = {}
            for field_name, field in self.form.fields.items():
                initial_data[field_name] = self.form.get_initial_for_field(
                    field, field_name
                )
            initial_form = self.form_class(initial_data, user=self.request.user)

            if initial_form.is_valid():
                queryset = query.patient_specific(patient_queryset=queryset,
                                                  **initial_form.cleaned_data)
                queryset = query.tumor_specific(patient_queryset=queryset,
                                                **initial_form.cleaned_data)
                queryset, combined_involvement = query.diagnose_specific(
                    patient_queryset=queryset, **initial_form.cleaned_data
                )
                queryset, counts = query.count_patients(
                    patient_queryset=queryset,
                    combined_involvement=combined_involvement
                )
                self.stats = counts

            else:
                self.logger.warn("Initial form is invalid, errors are: "
                                 f"{initial_form.errors.as_data()}")
                queryset = Patient.objects.none()

        end_querying = time.perf_counter()
        self.logger.info(
            f'Querying finished in {end_querying - start_querying:.3f} seconds'
        )
        return queryset

    def get_context_data(self) -> Dict[str, Any]:
        """Pass form and stats to the context. No need to have the list of
        patients in there too.
        """
        context = {
            "form": self.form,
            "stats": self.stats,
            "modalities": list(Diagnose.Modalities),
        }

        if self.form.is_valid():
            context["show_percent"] = self.form.cleaned_data["show_percent"]

        return context

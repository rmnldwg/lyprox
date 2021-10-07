from django.http.response import HttpResponse
from django.views import generic
from django.shortcuts import render

import time
from typing import Any, Dict

from core.loggers import ViewLoggerMixin
from patients.models import Patient, Tumor, Diagnose
from accounts.models import Institution

from . import query
from.forms import DashboardForm


def help_view(request) -> HttpResponse:
    """Simply display the help text."""
    template_name = "dashboard/help.html"
    return render(request, template_name)


class DashboardView(ViewLoggerMixin, generic.ListView):
    """View for extracting all patients that match the possibly complicated 
    selection criteria chosen by the user and creates the statistics and 
    displays of interest from it.
    """
    model = Patient  #:
    form_class = DashboardForm  #:
    context_object_name = "patient_list"  #:
    template_name = "dashboard/layout.html"  #:
    action = "display_dashboard"  #:

    def get_queryset(self):
        """Use the cleaned form data to narrow down the set of all patients in 
        the database.
        
        See Also:
            :py:func:`dashboard.query.patient_specific`: First part of querying 
                where patients are selected based on person-specific 
                characteristics.
            :py:func:`dashboard.query.tumor_specific`: Choose patients who's 
                tumors match selected criteria.
            :py:func:`dashboard.query.diagnose_specific`: Then, narrow it down 
                further by the selected patterns of involvement and combine 
                the chosen diagnostic modalities appropriately.
            :py:func:`dashboard.query.n_zero_specific`: This is finally used 
                to select N+ or N0 patients if that is of interest to the user.
            :py:func:`dashboard.query.count_patients`: Create the statistics 
                using the final queryset and combined involvement data.
        """
        self.form = self.form_class(self.request.GET or None)
        queryset = self.model.objects.all()
        start_querying = time.time()

        if self.request.method == "GET" and self.form.is_valid():
            queryset = query.patient_specific(
                patient_queryset=queryset, **self.form.cleaned_data
            )
            queryset = query.tumor_specific(
                patient_queryset=queryset, **self.form.cleaned_data
            )
            queryset, combined_involvement = query.diagnose_specific(
                patient_queryset=queryset, 
                cleaned_data=self.form.cleaned_data
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
            initial_form = self.form_class(initial_data)

            if initial_form.is_valid():
                queryset = query.patient_specific(patient_queryset=queryset, 
                                                  **initial_form.cleaned_data)
                queryset = query.tumor_specific(patient_queryset=queryset,
                                                **initial_form.cleaned_data)
                queryset, combined_involvement = query.diagnose_specific(
                    patient_queryset=queryset, 
                    cleaned_data=initial_form.cleaned_data
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
        
        end_querying = time.time()
        self.logger.info(
            f'Querying finished in {end_querying - start_querying:.3f} seconds'
        ) 
        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Pass all necessary context to the template renderer."""
        context = super(DashboardView, self).get_context_data(**kwargs)
        context["show_filter"] = False
        context["form"] = self.form
        # context["institutions"] = Institution.objects.all()
        
        if self.form.is_valid():
            context["show_percent"] = self.form.cleaned_data["show_percent"]
            
        context["stats"] = self.stats
        return context

    def get_template_names(self) -> str:
        """Depending on whether the user wants to see the dashboard with its 
        visualizations or just a list of the selected patients, choose the 
        corresponding HTML template for that.
        """
        if self.request.GET.get("render") == "subset_list":
            return "patients/list.html"
        else:
            return super(DashboardView, self).get_template_names()

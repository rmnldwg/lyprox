from django.views import generic

import time
from typing import Any, Dict

from core.loggers import ViewLoggerMixin
from patients.models import Patient, Tumor, Diagnose
from accounts.models import Institution

from . import query
from.forms import DashboardForm


class DashboardView(ViewLoggerMixin, generic.ListView):
    model = Patient
    form_class = DashboardForm
    context_object_name = "patient_list"
    template_name = "dashboard/layout.html"
    action = "display_dashboard"

    def get_queryset(self):
        self.form = self.form_class(self.request.GET or None)
        queryset = Patient.objects.all()
        start_querying = time.time()

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
            initial_form = self.form_class(initial_data)

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
        
        end_querying = time.time()
        self.logger.info(
            f'Querying finished in {end_querying - start_querying:.3f} seconds'
        ) 
        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super(DashboardView, self).get_context_data(**kwargs)
        context["show_filter"] = False
        context["form"] = self.form
        context["institutions"] = Institution.objects.all()
        
        if self.form.is_valid():
            context["show_percent"] = self.form.cleaned_data["show_percent"]
            
        context["stats"] = self.stats
        return context

    def get_template_names(self) -> str:
        if self.request.GET.get("render") == "subset_list":
            return "patients/list.html"
        else:
            return super(DashboardView, self).get_template_names()

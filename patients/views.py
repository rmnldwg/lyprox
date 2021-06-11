# from lymph_interface import patients
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from django.urls.base import reverse, reverse_lazy
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

import django_filters

from typing import Any, Dict, List, Optional, Sequence
import time
from numpy import e, errstate
import logging
logger = logging.getLogger(__name__)

from .models import Patient, Tumor, Diagnose, MODALITIES
from .forms import PatientForm, TumorForm, DiagnoseForm, DataFileForm, DashboardForm, ValidationError
from .utils import create_from_pandas, query, query2statistics
from .filters import PatientFilter


# PATIENT related views
class PatientListView(generic.ListView):
    model = Patient
    template_name = "patients/list.html"
    context_object_name = "patient_list"
    filterset_class = PatientFilter
    
    def get_queryset(self):
        """Add ability to filter queryset via FilterSets to generic ListView."""
        queryset = super().get_queryset()
        self.filterset = self.filterset_class(self.request.GET, 
                                              queryset=queryset)
        return self.filterset.qs.distinct()
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add FilterSet to context for displaying filter form."""
        context = super().get_context_data(**kwargs)
        context["filterset"] = self.filterset
        context["show_filter"] = True
        return context
    
    
class PatientDetailView(generic.DetailView):
    model = Patient
    template_name = "patients/patient_detail.html"
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        
        tumors = Tumor.objects.all().filter(patient=context["patient"])
        context["tumors"] = tumors
        
        diagnoses = Diagnose.objects.all().filter(patient=context["patient"])
        context["diagnoses"] = diagnoses
        
        return context


class CreatePatientView(LoginRequiredMixin, generic.CreateView):
    model = Patient
    form_class = PatientForm
    template_name = "patients/patient_form.html"
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["action"] = "create_patient"
        return context
    
      
class UpdatePatientView(LoginRequiredMixin, generic.UpdateView):
    model = Patient
    form_class = PatientForm
    template_name = "patients/patient_form.html"
    
    def get_success_url(self) -> str:
        return reverse("patients:detail", kwargs=self.kwargs)
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["action"] = "edit_patient"
        return context
    
    
class DeletePatientView(LoginRequiredMixin, generic.DeleteView):
    model = Patient
    template_name = "patients/patient_delete.html"
    success_url = "/patients"
    
    
class DashboardView(generic.ListView):
    model = Patient
    form_class = DashboardForm
    context_object_name = "patient_list"
    template_name = "patients/dashboard.html"

    def get_queryset(self):
        self.form = self.form_class(self.request.GET or None)

        if self.request.method == "GET" and self.form.is_valid():
            match_pats, match_diag_dict = query(
                self.form.cleaned_data
            )
            self.stats = query2statistics(match_pats,
                                          match_diag_dict,
                                          **self.form.cleaned_data)
            queryset = match_pats

        else:
            # fill form with initial values from respective form fields
            initial_data = {}
            for field_name, field in self.form.fields.items():
                initial_data[field_name] = self.form.get_initial_for_field(
                    field, field_name
                )
            initial_form = self.form_class(initial_data)

            if initial_form.is_valid():
                init_pats, init_diag_dict = query(
                    initial_form.cleaned_data
                )
                self.stats = query2statistics(init_pats,
                                              init_diag_dict,
                                              **initial_form.cleaned_data)
                queryset = init_pats

            else:
                msg = "Validation of default values of form failed."
                logger.error(msg)
                raise ValidationError(msg)

        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super(DashboardView, self).get_context_data(**kwargs)
        context["show_filter"] = False
        context["form"] = self.form
        context["stats"] = self.stats
        return context

    def get_template_names(self) -> str:
        if self.request.GET.get("render") == "subset_list":
            return "patients/list.html"
        else:
            return super(DashboardView, self).get_template_names()


@login_required
def upload_patients(request):
    """View to load many patients at once from a CSV file using pandas. This 
    requires the CSV file to be formatted in a certain way."""
    if request.method == "POST":
        form = DataFileForm(request.POST, request.FILES)
        
        # custom validator creates pandas DataFrame from uploaded CSV
        if form.is_valid():
            data_frame = form.cleaned_data["data_frame"]
            # creating patients from the resulting pandas DataFrame
            num_new, num_skipped = create_from_pandas(data_frame)
            context = {"upload_success": True, 
                       "num_new": num_new, 
                       "num_skipped": num_skipped}
            return render(request, "patients/upload.html", context)
        
    else:
        form = DataFileForm()
        
    context = {"upload_succes": False, "form": form}
    return render(request, "patients/upload.html", context)
    
    
# TUMOR related views
class CreateTumorView(LoginRequiredMixin, generic.CreateView):
    model = Tumor
    form_class = TumorForm
    template_name = "patients/patient_detail.html"

    def form_valid(self, form: TumorForm) -> HttpResponse:
        # assign tumor to current patient
        tumor = form.save(commit=False)
        tumor.patient = Patient.objects.get(**self.kwargs)
        
        # udate T-stage to always be the worst of a patient's tumors
        if tumor.patient.t_stage < tumor.t_stage:
            tumor.patient.t_stage = tumor.t_stage
            tumor.patient.save()
            
        return super(CreateTumorView, self).form_valid(form)

    def get_success_url(self) -> str:
        return reverse("patients:detail", kwargs=self.kwargs)
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["action"] = "create_tumor"
        
        patient = Patient.objects.get(**self.kwargs)
        context["patient"] = patient
        
        tumors = Tumor.objects.all().filter(patient=patient)
        context["tumors"] = tumors
        
        diagnoses = Diagnose.objects.all().filter(patient=patient)
        context["diagnoses"] = diagnoses
        
        return context
    
    
class UpdateTumorView(LoginRequiredMixin, generic.UpdateView):
    model = Tumor
    form_class = TumorForm
    template_name = "patients/patient_detail.html"
    
    def get_object(self):
        return Tumor.objects.get(pk=self.kwargs["tumor_pk"])
    
    def get_success_url(self) -> str:
        return reverse("patients:detail", 
                       kwargs={"pk": self.kwargs["pk"]})
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["action"] = "update_tumor"
        
        patient = Patient.objects.get(pk=self.kwargs["pk"])
        context["patient"] = patient
        
        tumors = Tumor.objects.all().filter(
            patient=patient
        ).exclude(
            pk=self.kwargs["tumor_pk"]
        )
        context["tumors"] = tumors
        
        diagnoses = Diagnose.objects.all().filter(patient=patient)
        context["diagnoses"] = diagnoses

        return context
    
    
class DeleteTumorView(LoginRequiredMixin, generic.DeleteView):
    model = Tumor
    template_name = "patients/patient_detail.html"
    
    def get_object(self):
        return Tumor.objects.get(pk=self.kwargs["tumor_pk"])
    
    def get_success_url(self) -> str:
        # get patient and...
        patient = Patient.objects.get(pk=self.kwargs["pk"])
        tumors = Tumor.objects.all().filter(
            patient=patient
        ).exclude(
            pk=self.kwargs["tumor_pk"]
        )
        # ...the new maximum T-stage to...
        max_t_stage = 0
        for tumor in tumors:
            if tumor.t_stage > max_t_stage:
                max_t_stage = tumor.t_stage
        # ...update the patient's T-stage after deletion. 
        patient.t_stage = max_t_stage
        patient.save()
        return reverse("patients:detail", kwargs={"pk": self.kwargs["pk"]})
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["action"] = "delete_tumor"
        
        patient = Patient.objects.get(pk=self.kwargs["pk"])
        context["patient"] = patient
        
        tumors = Tumor.objects.all().filter(
            patient=patient
        ).exclude(
            pk=self.kwargs["tumor_pk"]
        )
        context["tumors"] = tumors
        
        diagnoses = Diagnose.objects.all().filter(patient=patient)
        context["diagnoses"] = diagnoses

        return context


# DIAGNOSE related views
class CreateDiagnoseView(LoginRequiredMixin, generic.CreateView):
    model = Diagnose
    form_class = DiagnoseForm
    template_name = "patients/patient_detail.html"

    def form_valid(self, form: DiagnoseForm) -> HttpResponse:
        diagnose = form.save(commit=False)
        diagnose.patient = Patient.objects.get(**self.kwargs)
        return super(CreateDiagnoseView, self).form_valid(form)

    def get_success_url(self) -> str:
        return reverse("patients:detail", kwargs=self.kwargs)
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["action"] = "create_diagnose"
        
        patient = Patient.objects.get(**self.kwargs)
        context["patient"] = patient
        
        tumors = Tumor.objects.all().filter(patient=patient)
        context["tumors"] = tumors
        
        diagnoses = Diagnose.objects.all().filter(patient=patient)
        context["diagnoses"] = diagnoses
        
        return context
    
    
class UpdateDiagnoseView(LoginRequiredMixin, generic.UpdateView):
    model = Diagnose
    form_class = DiagnoseForm
    template_name = "patients/patient_detail.html"
    
    def get_object(self):
        return Diagnose.objects.get(pk=self.kwargs["diagnose_pk"])
    
    def get_success_url(self) -> str:
        return reverse("patients:detail", 
                       kwargs={"pk": self.kwargs["pk"]})
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["action"] = "update_diagnose"
        
        patient = Patient.objects.get(pk=self.kwargs["pk"])
        context["patient"] = patient
        
        tumors = Tumor.objects.all().filter(patient=patient)
        context["tumors"] = tumors
        
        diagnoses = Diagnose.objects.all().filter(
            patient=patient
        ).exclude(
            pk=self.kwargs["diagnose_pk"]
        )
        context["diagnoses"] = diagnoses

        return context
    
    
class DeleteDiagnoseView(LoginRequiredMixin, generic.DeleteView):
    model = Diagnose
    template_name = "patients/patient_detail.html"
    
    def get_object(self):
        return Diagnose.objects.get(pk=self.kwargs["diagnose_pk"])
    
    def get_success_url(self) -> str:
        return reverse("patients:detail", kwargs={"pk": self.kwargs["pk"]})
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["action"] = "delete_diagnose"
        
        patient = Patient.objects.get(pk=self.kwargs["pk"])
        context["patient"] = patient
        
        tumors = Tumor.objects.all().filter(patient=patient)
        context["tumors"] = tumors
        
        diagnoses = Diagnose.objects.all().filter(
            patient=patient
        ).exclude(
            pk=self.kwargs["diagnose_pk"]
        )
        context["diagnoses"] = diagnoses

        return context

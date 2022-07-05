"""
Here, the generic views from ``django.views.generic`` are implemented for the
``patients.models``.

A view handles the actual rendering of the HTML template that needs to be
filled with what the python backend computes/generates.

It includes views for creating, editing, deleting and
listing the models in the ``patients`` app.
"""
# pylint: disable=no-member
# pylint: disable=logging-fstring-interpolation

import logging
import time
from pathlib import Path
from typing import Any, Dict

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.query import QuerySet
from django.http import FileResponse, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.urls.base import reverse
from django.views import View, generic

from accounts.mixins import (
    InstitutionCheckObjectMixin,
    InstitutionCheckPatientMixin,
)
from core.loggers import ViewLoggerMixin
from dashboard import query
from dashboard.forms import DashboardForm

from .filters import PatientFilter
from .forms import DatasetForm, DiagnoseForm, PatientForm, TumorForm
from .models import Dataset, Diagnose, Patient, Tumor

logger = logging.getLogger(__name__)


# DATASET related views
class CreateDatasetView(
    ViewLoggerMixin,
    LoginRequiredMixin,
    generic.CreateView
):
    """Create a dataset from a form."""
    model = Dataset
    form_class = DatasetForm
    template_name = "patients/dataset_form.html"
    success_url = "/patients/dataset"

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

class DatasetListView(ViewLoggerMixin, generic.ListView):
    """
    View that displays all datasets in a list.
    """
    model = Dataset
    template_name: str = "patients/dataset_patient_list.html"

    def get_queryset(self):
        """
        Return the tables available for download, based on the (logged in) user.
        """
        queryset = Dataset.objects.all()
        user = self.request.user

        if not user.is_authenticated:
            queryset = queryset.filter(is_public=True)

        return queryset

class DatasetView(ViewLoggerMixin, View):
    """
    View that serves the respective `Dataset` CSV file.
    """
    def get(self, request, relative_path):
        """
        Get correct table and render download response.
        """
        kwargs = {}
        if "uploads" in relative_path:
            kwargs["upload_csv"] = relative_path
        elif "exports" in relative_path:
            kwargs["export_csv"] = relative_path

        dataset = get_object_or_404(Dataset, **kwargs)
        if not dataset.is_public and not request.user.is_authenticated:
            return HttpResponseForbidden()

        absolute_path = Path(f"{settings.MEDIA_ROOT}/{relative_path}")
        csv_file = open(absolute_path, 'rb')
        response = FileResponse(csv_file, as_attachment=True)
        return response


# PATIENT related views
class PatientListView(ViewLoggerMixin, generic.ListView):
    """
    Renders a list of all patients in the database showing basic information
    and links to the individual entries. Depending from where this view is
    called, the list is filterable.
    """
    model = Patient
    form_class = DashboardForm
    filterset_class = PatientFilter
    template_name = "patients/patient_list.html"
    context_object_name = "patient_list"
    action = "show_patient_list"
    is_filterable = True
    queryset_pk_list = []

    def get_queryset(self) -> QuerySet[Patient]:
        """Add ability to filter queryset via FilterSets to generic ListView."""
        queryset = super().get_queryset()
        start_querying = time.perf_counter()

        if not self.request.user.is_authenticated:
            queryset = queryset.filter(dataset__is_public=True)

        self.filterset = self.filterset_class(
            self.request.GET or None, queryset, request=self.request,
        )
        self.form = self.form_class(
            self.request.GET or None, user=self.request.user,
        )

        if self.filterset.is_valid():
            queryset = self.filterset.qs.distinct()

        if self.form.is_valid():
            self.is_filterable = False
            queryset = query.patient_specific(
                patient_queryset=queryset, **self.form.cleaned_data
            )
            queryset = query.tumor_specific(
                patient_queryset=queryset, **self.form.cleaned_data
            )
            queryset, combined_involvement = query.diagnose_specific(
                patient_queryset=queryset, **self.form.cleaned_data
            )
            queryset, _ = query.n_zero_specific(
                patient_queryset=queryset,
                combined_involvement=combined_involvement,
                n_status=self.form.cleaned_data['n_status']
            )

        self.queryset_pk_list = list(queryset.values_list("pk", flat=True))
        self.logger.debug(",".join(str(pk) for pk in self.queryset_pk_list))

        end_querying = time.perf_counter()
        self.logger.info(
            f'Querying finished in {end_querying - start_querying:.3f} seconds'
        )
        return queryset


    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add FilterSet to context for displaying filter form."""
        context = super().get_context_data(**kwargs)

        context["queryset_pk_list"] = self.queryset_pk_list
        context["is_filterable"] = self.is_filterable
        if self.is_filterable:
            context["filterset"] = self.filterset

        return context


class PatientDetailView(generic.DetailView):
    """Show details of a particular patient."""
    model = Patient
    template_name = "patients/patient_detail.html"  #:
    action = "show_patient_detail"  #:


class CreatePatientView(ViewLoggerMixin,
                        LoginRequiredMixin,
                        generic.CreateView):
    """View used to create a new patient entry in the database."""
    model = Patient
    form_class = PatientForm
    template_name = "patients/patient_form.html"  #:
    action = "create_patient"  #:

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add ``action`` to context for rendering purposes."""
        context = super().get_context_data(**kwargs)
        context["action"] = self.action
        return context

    def get_form_kwargs(self) -> Dict[str, Any]:
        """Pass user to form, so that a newly created patient can be assigned
        to the same institution as the user who created them."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class UpdatePatientView(ViewLoggerMixin,
                        LoginRequiredMixin,
                        InstitutionCheckPatientMixin,
                        generic.UpdateView):
    """Update a given patient's information."""
    model = Patient
    form_class = PatientForm
    template_name = "patients/patient_form.html"  #:
    action = "edit_patient"  #:

    def get_success_url(self) -> str:
        """When successfully edited, redirect to that patient's
        :class:`PatientDetailView`"""
        return reverse("patients:detail", kwargs=self.kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add ``action`` to context for rendering purposes."""
        context = super().get_context_data(**kwargs)
        context["action"] = self.action
        return context

    def get_form_kwargs(self) -> Dict[str, Any]:
        """Pass current user to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class DeletePatientView(ViewLoggerMixin,
                        LoginRequiredMixin,
                        InstitutionCheckPatientMixin,
                        generic.DeleteView):
    """Remove this patient from the database."""
    model = Patient
    template_name = "patients/patient_delete.html"  #:
    success_url = "/patients"  #:
    action = "delete_patient"  #:


# TUMOR related views
class CreateTumorView(ViewLoggerMixin,
                      LoginRequiredMixin,
                      InstitutionCheckObjectMixin,
                      generic.CreateView):
    """Create a tumor and add it to a given patient."""
    model = Tumor
    form_class = TumorForm
    template_name = "patients/patient_detail.html"  #:
    action = "create_tumor"  #:

    def form_valid(self, form: TumorForm) -> HttpResponse:
        """After form validation, add the tumor to the given patient."""
        # assign tumor to current patient
        tumor = form.save(commit=False)
        tumor.patient = Patient.objects.get(**self.kwargs)

        return super(CreateTumorView, self).form_valid(form)

    def get_success_url(self) -> str:
        """After successfull creation, redirect to the patient's detail view
        that also contains info about this tumor."""
        return reverse("patients:detail", kwargs=self.kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add this tumor's patient, the patient's tumor and diagnoses, as well
        as the currently performed action to the context dictionary."""
        context = super().get_context_data(**kwargs)
        context["action"] = self.action

        patient = Patient.objects.get(**self.kwargs)
        context["patient"] = patient

        tumors = Tumor.objects.all().filter(patient=patient)
        context["tumors"] = tumors

        diagnoses = Diagnose.objects.all().filter(patient=patient)
        context["diagnoses"] = diagnoses

        return context


class UpdateTumorView(ViewLoggerMixin,
                      LoginRequiredMixin,
                      InstitutionCheckObjectMixin,
                      generic.UpdateView):
    """Update specifics of a patient's tumor."""
    model = Tumor
    form_class = TumorForm
    template_name = "patients/patient_detail.html"  #:
    action = "update_tumor"  #:

    def get_object(self):
        """Get tumor by ``PK``."""
        return Tumor.objects.get(pk=self.kwargs["tumor_pk"])

    def get_success_url(self) -> str:
        """After successfully updating the tumor, redirect to patient's detail
        view."""
        return reverse("patients:detail",
                       kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add this tumor's patient, the patient's tumor and diagnoses, as well
        as the currently performed action to the context dictionary."""
        context = super().get_context_data(**kwargs)
        context["action"] = self.action

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


class DeleteTumorView(ViewLoggerMixin,
                      LoginRequiredMixin,
                      InstitutionCheckObjectMixin,
                      generic.DeleteView):
    """Delete a patient's tumor."""
    model = Tumor
    template_name = "patients/patient_detail.html"
    action = "delete_tumor"

    def get_object(self):
        """Get tumor by ``PK``."""
        return Tumor.objects.get(pk=self.kwargs["tumor_pk"])

    def get_success_url(self) -> str:
        """After successfully updating the tumor, redirect to patient's detail
        view."""
        return reverse("patients:detail", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add this tumor's patient, the patient's tumor and diagnoses, as well
        as the currently performed action to the context dictionary."""
        context = super().get_context_data(**kwargs)
        context["action"] = self.action

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
class CreateDiagnoseView(ViewLoggerMixin,
                         LoginRequiredMixin,
                         InstitutionCheckObjectMixin,
                         generic.CreateView):
    """Add a diagnose for a patient's lymphatic system."""
    model = Diagnose
    form_class = DiagnoseForm
    template_name = "patients/patient_detail.html"  #:
    action = "create_diagnose"  #:

    def form_valid(self, form: DiagnoseForm) -> HttpResponse:
        """As with the tumor, add the diagnose to the already existing patient
        after the form was validated."""
        diagnose = form.save(commit=False)
        diagnose.patient = Patient.objects.get(**self.kwargs)
        return super(CreateDiagnoseView, self).form_valid(form)

    def get_success_url(self) -> str:
        """After successfully updating the diagnose, redirect to patient's
        detail view."""
        return reverse("patients:detail", kwargs=self.kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add this diagnose's patient, the patient's tumor and diagnoses, as
        well as the currently performed action to the context dictionary."""
        context = super().get_context_data(**kwargs)
        context["action"] = self.action

        patient = Patient.objects.get(**self.kwargs)
        context["patient"] = patient

        tumors = Tumor.objects.all().filter(patient=patient)
        context["tumors"] = tumors

        diagnoses = Diagnose.objects.all().filter(patient=patient)
        context["diagnoses"] = diagnoses

        return context


class UpdateDiagnoseView(ViewLoggerMixin,
                         LoginRequiredMixin,
                         InstitutionCheckObjectMixin,
                         generic.UpdateView):
    """Change a patient's diagnose."""
    model = Diagnose
    form_class = DiagnoseForm
    template_name = "patients/patient_detail.html"  #:
    action = "update_diagnose"  #:

    def get_object(self):
        """Get diagnose by ``PK``."""
        return Diagnose.objects.get(pk=self.kwargs["diagnose_pk"])

    def get_success_url(self) -> str:
        """After successfully updating the diagnose, redirect to patient's
        detail view."""
        return reverse("patients:detail",
                       kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add this diagnose's patient, the patient's tumor and diagnoses, as
        well as the currently performed action to the context dictionary."""
        context = super().get_context_data(**kwargs)
        context["action"] = self.action

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


class DeleteDiagnoseView(ViewLoggerMixin,
                         LoginRequiredMixin,
                         InstitutionCheckObjectMixin,
                         generic.DeleteView):
    """Remove a particular diagnose frm a patient's entry."""
    model = Diagnose
    template_name = "patients/patient_detail.html"  #:
    action = "delete_diagnose"  #:

    def get_object(self):
        """Get diagnose by ``PK``."""
        return Diagnose.objects.get(pk=self.kwargs["diagnose_pk"])

    def get_success_url(self) -> str:
        """After successfully updating the diagnose, redirect to patient's
        detail view."""
        return reverse("patients:detail", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add this diagnose's patient, the patient's tumor and diagnoses, as
        well as the currently performed action to the context dictionary."""
        context = super().get_context_data(**kwargs)
        context["action"] = self.action

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

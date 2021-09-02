from django.shortcuts import render
from django.http import HttpResponse
from django.urls.base import reverse
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.conf import settings

from typing import Any, Dict, Optional
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

from .models import Patient, Tumor, Diagnose
from .forms import (PatientForm, 
                    TumorForm, 
                    DiagnoseForm, 
                    DataFileForm)
from .ioports import export_to_pandas, import_from_pandas, ParsingError
from .filters import PatientFilter
from core.loggers import ViewLoggerMixin


# PATIENT related views
class PatientListView(generic.ListView):
    model = Patient
    template_name = "patients/list.html"
    context_object_name = "patient_list"
    filterset_class = PatientFilter
    action = "show_patient_list"
    
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
    action = "show_patient_detail"
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        
        tumors = Tumor.objects.all().filter(patient=context["patient"])
        context["tumors"] = tumors
        
        diagnoses = Diagnose.objects.all().filter(patient=context["patient"])
        context["diagnoses"] = diagnoses
        
        return context


class CreatePatientView(ViewLoggerMixin, 
                        LoginRequiredMixin, 
                        generic.CreateView):
    model = Patient
    form_class = PatientForm
    template_name = "patients/patient_form.html"
    action = "create_patient"
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["action"] = self.action
        return context
    
      
class UpdatePatientView(ViewLoggerMixin, 
                        LoginRequiredMixin, 
                        UserPassesTestMixin,
                        generic.UpdateView):
    model = Patient
    form_class = PatientForm
    template_name = "patients/patient_form.html"
    action = "edit_patient"
    
    def get_success_url(self) -> str:
        return reverse("patients:detail", kwargs=self.kwargs)
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["action"] = self.action
        return context
    
    def test_func(self) -> Optional[bool]:
        """Make sure editing user is either superuser or comes from the 
        institution that added the user in the first place."""
        user = self.request.user
        if user.is_superuser:
            return True
        
        user_institution = user.institution
        patient_institution = self.object.institution
        return user_institution == patient_institution
    
    
class DeletePatientView(ViewLoggerMixin, 
                        LoginRequiredMixin, 
                        UserPassesTestMixin,
                        generic.DeleteView):
    model = Patient
    template_name = "patients/patient_delete.html"
    success_url = "/patients"
    action = "delete_patient"
    
    def test_func(self) -> Optional[bool]:
        """Make sure editing user is either superuser or comes from the 
        institution that added the user in the first place."""
        user = self.request.user
        if user.is_superuser:
            return True
        
        user_institution = user.institution
        patient_institution = self.object.institution
        return user_institution == patient_institution


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
            try:
                num_new, num_skipped = import_from_pandas(data_frame)
            except ParsingError as pe:
                logger.error(pe.message)
                form = DataFileForm()
                context = {"upload_success": False, 
                           "form": form, 
                           "error": pe.message}
                return render(request, "patients/upload.html", context)
                
            context = {"upload_success": True, 
                       "num_new": num_new, 
                       "num_skipped": num_skipped}
            return render(request, "patients/upload.html", context)
        
    else:
        form = DataFileForm()
        
    context = {"upload_succes": False, "form": form}
    return render(request, "patients/upload.html", context)


@login_required
def generate_and_download_csv(request):
    """Allow user to generate a CSV table from the current database and 
    download it."""
    
    # NOTE: This is only possible as long as the static files are served from 
    #   the same directory as the root directory of the django app.
    # download_folder = settings.MEDIA_ROOT / "downloads"
    download_file_path = settings.DOWNLOADS_ROOT / "latest.csv"
    context = {}
    
    if request.method == "POST":
        try:
            patient_df = export_to_pandas(Patient.objects.all())
            patient_df.to_csv(download_file_path, index=False)
            logger.info("Successfully generated and saved database as CSV.")
            context["generate_success"] = True
            
        except FileNotFoundError:
            msg = ("Download folder is missing or can't be accessed.")
            logger.error(msg)
            context["generate_success"] = False
            context["error"] = msg
                
        except Exception as e:
            logger.error(e)
            context["generate_success"] = False
            context["error"] = e
    
    context["download_available"] = Path(download_file_path).is_file()
    return render(request, "patients/download.html", context)
    
    
# TUMOR related views
class CreateTumorView(ViewLoggerMixin, 
                      LoginRequiredMixin,
                      generic.CreateView):
    model = Tumor
    form_class = TumorForm
    template_name = "patients/patient_detail.html"
    action = "create_tumor"

    def form_valid(self, form: TumorForm) -> HttpResponse:
        # assign tumor to current patient
        tumor = form.save(commit=False)
        tumor.patient = Patient.objects.get(**self.kwargs)
            
        return super(CreateTumorView, self).form_valid(form)

    def get_success_url(self) -> str:
        return reverse("patients:detail", kwargs=self.kwargs)
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["action"] = self.action
        
        patient = Patient.objects.get(**self.kwargs)
        context["patient"] = patient
        
        tumors = Tumor.objects.all().filter(patient=patient)
        context["tumors"] = tumors
        
        diagnoses = Diagnose.objects.all().filter(patient=patient)
        context["diagnoses"] = diagnoses
        
        return context
    
    
class UpdateTumorView(ViewLoggerMixin, LoginRequiredMixin, generic.UpdateView):
    model = Tumor
    form_class = TumorForm
    template_name = "patients/patient_detail.html"
    action = "update_tumor"
    
    def get_object(self):
        return Tumor.objects.get(pk=self.kwargs["tumor_pk"])
    
    def get_success_url(self) -> str:
        return reverse("patients:detail", 
                       kwargs={"pk": self.kwargs["pk"]})
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
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
    
    
class DeleteTumorView(ViewLoggerMixin, LoginRequiredMixin, generic.DeleteView):
    model = Tumor
    template_name = "patients/patient_detail.html"
    action = "delete_tumor"
    
    def get_object(self):
        return Tumor.objects.get(pk=self.kwargs["tumor_pk"])
    
    def get_success_url(self) -> str:
        return reverse("patients:detail", kwargs={"pk": self.kwargs["pk"]})
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
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
class CreateDiagnoseView(ViewLoggerMixin, LoginRequiredMixin, generic.CreateView):
    model = Diagnose
    form_class = DiagnoseForm
    template_name = "patients/patient_detail.html"
    action = "create_diagnose"

    def form_valid(self, form: DiagnoseForm) -> HttpResponse:
        diagnose = form.save(commit=False)
        diagnose.patient = Patient.objects.get(**self.kwargs)
        return super(CreateDiagnoseView, self).form_valid(form)

    def get_success_url(self) -> str:
        return reverse("patients:detail", kwargs=self.kwargs)
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["action"] = self.action
        
        patient = Patient.objects.get(**self.kwargs)
        context["patient"] = patient
        
        tumors = Tumor.objects.all().filter(patient=patient)
        context["tumors"] = tumors
        
        diagnoses = Diagnose.objects.all().filter(patient=patient)
        context["diagnoses"] = diagnoses
        
        return context
    
    
class UpdateDiagnoseView(ViewLoggerMixin, LoginRequiredMixin, generic.UpdateView):
    model = Diagnose
    form_class = DiagnoseForm
    template_name = "patients/patient_detail.html"
    action = "update_diagnose"
    
    def get_object(self):
        return Diagnose.objects.get(pk=self.kwargs["diagnose_pk"])
    
    def get_success_url(self) -> str:
        return reverse("patients:detail", 
                       kwargs={"pk": self.kwargs["pk"]})
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
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
    
    
class DeleteDiagnoseView(ViewLoggerMixin, LoginRequiredMixin, generic.DeleteView):
    model = Diagnose
    template_name = "patients/patient_detail.html"
    action = "delete_diagnose"
    
    def get_object(self):
        return Diagnose.objects.get(pk=self.kwargs["diagnose_pk"])
    
    def get_success_url(self) -> str:
        return reverse("patients:detail", kwargs={"pk": self.kwargs["pk"]})
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
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

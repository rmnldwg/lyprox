# from lymph_interface import patients
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from django.urls.base import reverse, reverse_lazy
from django.views import generic

from typing import Any, Dict, List, Optional

import time

from numpy import e, errstate

from .models import Patient, Tumor, Diagnose, MODALITIES
from .forms import PatientForm, TumorForm, DiagnoseForm, DataFileForm, DashboardForm, ValidationError
from .utils import create_from_pandas, query, query2statistics


# PATIENT related views
class ListView(generic.ListView):
    template_name = "patients/list.html"
    context_object_name = "patient_list"
    
    def get_queryset(self, *args, **kwargs):
        """List all patients in the database."""
        try:
            queryset = kwargs["queryset"]
        except KeyError:
            queryset = Patient.objects.all()
        return queryset
    
    
class DetailView(generic.DetailView):
    model = Patient
    template_name = "patients/patient_detail.html"
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        
        tumors = Tumor.objects.all().filter(patient=context["patient"])
        context["tumors"] = tumors
        
        diagnoses = Diagnose.objects.all().filter(patient=context["patient"])
        context["diagnoses"] = diagnoses
        
        return context


class CreatePatientView(generic.CreateView):
    model = Patient
    form_class = PatientForm
    template_name = "patients/patient_form.html"
    
    # def get_success_url(self) -> str:
    #     return redirect("patients:detail", pk=self.kwargs["pk"])
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["action"] = "create_patient"
        return context
    
      
class UpdatePatientView(generic.UpdateView):
    model = Patient
    form_class = PatientForm
    template_name = "patients/patient_form.html"
    
    def get_success_url(self) -> str:
        return reverse("patients:detail", kwargs=self.kwargs)
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["action"] = "edit_patient"
        return context
    
    
class DeletePatientView(generic.DeleteView):
    model = Patient
    template_name = "patients/patient_delete.html"
    success_url = "/patients"


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
class CreateTumorView(generic.CreateView):
    model = Tumor
    form_class = TumorForm
    template_name = "patients/patient_detail.html"

    def form_valid(self, form: TumorForm) -> HttpResponse:
        tumor = form.save(commit=False)
        tumor.patient = Patient.objects.get(**self.kwargs)
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
    
    
class UpdateTumorView(generic.UpdateView):
    model = Tumor
    form_class = TumorForm
    template_name = "patients/patient_detail.html"
    
    def get_object(self):
        print(self.kwargs)
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
    
    
class DeleteTumorView(generic.DeleteView):
    model = Tumor
    template_name = "patients/patient_detail.html"
    
    def get_object(self):
        print(self.kwargs)
        return Tumor.objects.get(pk=self.kwargs["tumor_pk"])
    
    def get_success_url(self) -> str:
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
        

    
    
def change_tumor_of_patient(request, *args, **kwargs):
    """Edit or delete a patient's tumor."""

    if request.method == "POST":
        data = request.POST
        print(data)

        if "edit_pk" in data:
            print("editing...")
            patient = Patient.objects.get(**kwargs)
            
            tumor_pk = data["edit_pk"]
            tumor = Tumor.objects.get(pk=tumor_pk)
            tumor_form = TumorForm(instance=tumor)
            
            tumor.delete()
            
            context = {"action": "add_tumor",
                       "tumor_form": tumor_form,
                       "patient": patient}
            
            return render(request, "patients/detail.html", context)
            
        elif "delete_pk" in data:
            print("deleting...")
            tumor_pk = data["delete_pk"]
            tumor = Tumor.objects.get(pk=tumor_pk)
            tumor.delete()
            
            return redirect("patients:detail", pk=kwargs["pk"])
        else:
            raise ValidationError("Form was submitted without instructions.")
        
    else:
        return redirect("patients:detail", pk=kwargs["pk"])


def add_diagnose_to_patient(request, *args, **kwargs):
    """View to add new tumors and diagnoses to existing patients."""
    diagnose_form = DiagnoseForm(request.POST or None)
    
    if diagnose_form.is_valid():
        new_diagnose = diagnose_form.save(kwargs["pk"])
        diagnose_form = DiagnoseForm()
        
    context = {"action": "add_diagnose", 
               "diagnose_form": diagnose_form,
               "patient": Patient.objects.get(pk=kwargs["pk"])}
    return render(request, "patients/detail.html", context)


def edit_diagnose_of_patient(request, *args, **kwargs):
    """Edit an existing diagnose."""
    patient = Patient.objects.get(pk=kwargs["pk"])

    if request.method == "POST":
        diagnose = Diagnose.objects.get(pk=request.POST["diagnose_pk"])
        diagnose_form = DiagnoseForm(instance=diagnose)

        if diagnose.patient != patient:
            raise Exception("Find out which error to raise here!")

        diagnose.delete()

        context = {"action": "add_diagnose",
                   "diagnose_form": diagnose_form,
                   "patient": patient}

        return render(request, "patients/detail.html", context)

    else:
        return redirect("patients:detail", pk=patient.pk)
    
    
def change_diagnose_of_patient(request, *args, **kwargs):
    """Edit or delete a patient's diagnose."""

    if request.method == "POST":
        data = request.POST
        print(data)

        if "edit_pk" in data:
            print("editing...")
            patient = Patient.objects.get(pk=kwargs["pk"])

            diagnose_pk = data["edit_pk"]
            diagnose = Diagnose.objects.get(pk=diagnose_pk)
            diagnose_form = DiagnoseForm(instance=diagnose)

            diagnose.delete()

            context = {"action": "add_diagnose",
                       "diagnose_form": diagnose_form,
                       "patient": patient}

            return render(request, "patients/detail.html", context)

        elif "delete_pk" in data:
            print("deleting...")
            diagnose_pk = data["delete_pk"]
            diagnose = Diagnose.objects.get(pk=diagnose_pk)
            diagnose.delete()

            return redirect("patients:detail", pk=kwargs["pk"])
        else:
            raise ValidationError("Form was submitted without instructions.")

    else:
        return redirect("patients:detail", pk=kwargs["pk"])


def delete_diagnose_from_patient(request, *args, **kwargs):
    """Delete one specific diagnose from the list of diagnoses of a particular 
    patient."""
    patient = Patient.objects.get(pk=kwargs["pk"])
    
    if request.method == "POST":
        diagnose = Diagnose.objects.get(pk=request.POST["diagnose_pk"])
    
        if diagnose.patient != patient:
            raise Exception("Find out which error to raise here!")
    
        diagnose.delete()
    
    return redirect("patients:detail", pk=patient.pk)


def dashboard(request):
    """Display the dashboard showing patterns of involvement."""
    form = DashboardForm(request.POST or None)
    
    if request.method == "POST" and form.is_valid():
        match_patients, match_diagnoses_dict = query(form.cleaned_data)
        
        statistics = query2statistics(match_patients,
                                      match_diagnoses_dict,
                                      **form.cleaned_data)
        print(f"Query contains {len(match_patients)} patients, "
              f"{len(match_diagnoses_dict['ipsi'])} ipsilateral & "
              f"{len(match_diagnoses_dict['contra'])} contralateral diagnoses.")
    else:    
        initial_data = {}
        for field_name, field in form.fields.items():
            initial_data[field_name] = form.get_initial_for_field(field, field_name)
            
        initial_form = DashboardForm(initial_data)
        
        if initial_form.is_valid():
            init_patients, init_diagnoses_dict = query(initial_form.cleaned_data)
            statistics = query2statistics(init_patients, init_diagnoses_dict)
        else:
            raise ValidationError("Validation of default values of form failed.")

    context = {"form": form, 
               "stats": statistics}
        
    return render(request, "patients/dashboard.html", context)
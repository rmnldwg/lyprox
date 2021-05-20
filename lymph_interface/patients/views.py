from django.shortcuts import render, get_object_or_404, reverse, redirect
from django.http import HttpResponse, Http404
from django.views import generic

from typing import Any, Dict, List

import time

from .models import Patient, Tumor, Diagnose, MODALITIES
from .forms import PatientCreateForm, PatientForm, TumorForm, DiagnoseForm, DataFileForm, DashboardForm, ValidationError
from .utils import create_from_pandas, query, query2statistics


class ListView(generic.ListView):
    template_name = "patients/list.html"
    context_object_name = "patient_list"
    
    def get_queryset(self, patients=Patient.objects.all()):
        """List all patients in the database."""
        return patients
    
    
class DetailView(generic.DetailView):
    model = Patient
    template_name = "patients/patient_detail.html"


class CreatePatientView(generic.FormView):
    model = Patient
    form_class = PatientCreateForm
    template_name = "patients/patient_create.html"
    
    def get_success_url(self) -> str:
        return redirect("patients:detail", pk=self.kwargs["pk"])
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["create"] = True
        return context
    
    
class UpdatePatientView(generic.UpdateView):
    model = Patient
    form_class = PatientForm
    template_name = "patients/patient_create.html"
    
    def get_success_url(self) -> str:
        return redirect("patients:detail", pk=self.kwargs["pk"])
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["create"] = False
        return context
    
    
class DeletePatientView(generic.DeleteView):
    model = Patient
    template_name = "patients/patient_delete.html"
    success_url = "patients/"


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
    
    
def add_tumor_to_patient(request, *args, **kwargs):
    """View to add new tumors and diagnoses to existing patients."""
    tumor_form = TumorForm(request.POST or None)
    
    if tumor_form.is_valid():
        new_tumor = tumor_form.save(kwargs["pk"])
        tumor_form = TumorForm()
        
    context = {"action": "add_tumor", 
               "tumor_form": tumor_form, 
               "patient": Patient.objects.get(pk=kwargs["pk"])}
    return render(request, "patients/detail.html", context)
    
    
def change_tumor_of_patient(request, *args, **kwargs):
    """Edit or delete a patient's tumor."""

    if request.method == "POST":
        data = request.POST
        print(data)

        if "edit_pk" in data:
            print("editing...")
            patient = Patient.objects.get(pk=kwargs["pk"])
            
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
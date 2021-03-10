from django.shortcuts import render, get_object_or_404, reverse, redirect
from django.http import HttpResponse, Http404
from django.views import generic

from .models import Patient, Tumor, Diagnose
from .forms import PatientForm, TumorForm, DiagnoseForm, DataFileForm, DashboardForm
from .utils import create_from_pandas


class ListView(generic.ListView):
    template_name = "patients/list.html"
    context_object_name = "patient_list"
    
    def get_queryset(self):
        """List all patients in the database."""
        return Patient.objects.all()
    
    
    
class DetailView(generic.DetailView):
    model = Patient
    template_name = "patients/detail.html"
    
    
    
def create_patient(request):
    """View to add new patients to the database."""
    form = PatientForm(request.POST or None)
    
    if form.is_valid():
        new_patient = form.save()
        return redirect("patients:add_tumor", pk=new_patient.pk)
        
    context = {"form": form}
    return render(request, "patients/create.html", context)


def upload_patients(request):
    """View to load many patients at once from a CSV file using pandas. This 
    requires the CSV file to be formatted in a certain way."""
    if request.method == "POST":
        form = DataFileForm(request.POST, request.FILES)
        
        # custom validator creates pandas DataFrame from uploaded CSV
        if form.is_valid():
            data_frame = form.cleaned_data["data_frame"]
            # creating patients from the resulting pandas DataFrame
            num_new = create_from_pandas(data_frame)
            context = {"upload_success": True, "num_new": num_new}
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


def delete_tumor_from_patient(request, *args, **kwargs):
    """Delete one specific tumor from the list of tumors of a particular 
    patient."""
    patient = Patient.objects.get(pk=kwargs["pk"])
    
    if request.method == "POST":
        tumor = Tumor.objects.get(pk=request.POST["tumor_pk"])
    
        if tumor.patient != patient:
            raise Exception("Find out which error to raise here!")
    
        tumor.delete()
    
    return redirect("patients:detail", pk=patient.pk)


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
    if request.method == "POST":
        print(request.POST)
        form = DashboardForm(request)
    else:
        form = DashboardForm()

    context = {"form": form}
    return render(request, "patients/dashboard.html", context)
from django.shortcuts import render, get_object_or_404, reverse
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.views import generic

from .models import Patient
from .forms import PatientForm, TumorForm, DiagnoseForm

# Create your views here.
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
        return HttpResponseRedirect(reverse("patients:add_tumor", kwargs={"pk": new_patient.pk}))
        
    context = {"form": form}
    return render(request, "patients/create.html", context)
    
    
def add_tumor_to_patient(request, *args, **kwargs):
    """View to add new tumors and diagnoses to existing patients."""
    tumor_form = TumorForm(request.POST or None)
    
    if tumor_form.is_valid():
        new_tumor = tumor_form.save(kwargs["pk"])
        tumor_form = TumorForm()
        
    context = {"tumor_form": tumor_form, 
               "patient": Patient.objects.get(pk=kwargs["pk"])}
    return render(request, "patients/add_tumor.html", context)


def add_diagnose_to_patient(request, *args, **kwargs):
    """View to add new tumors and diagnoses to existing patients."""
    diagnose_form = DiagnoseForm(request.POST or None)
    
    if diagnose_form.is_valid():
        new_diagnose = diagnose_form.save(kwargs["pk"])
        diagnose_form = DiagnoseForm()
        
    context = {"diagnose_form": diagnose_form,
               "patient": Patient.objects.get(pk=kwargs["pk"])}
    return render(request, "patients/add_diagnose.html", context)
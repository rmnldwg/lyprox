from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from django.views import generic

from .models import Patient
from .forms import PatientForm

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
    form = PatientForm(request.POST or None)
    
    if form.is_valid():
        form.save()
        form = PatientForm()
        
    context = {"form": form}
    return render(request, "patients/create.html", context)
    
from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.views import generic

from .models import Patient

# Create your views here.
class IndexView(generic.ListView):
    template_name = "patients/index.html"
    context_object_name = "patient_list"
    
    def get_queryset(self):
        """List all patients in the database."""
        return Patient.objects.all()
    
    
class DetailView(generic.DetailView):
    model = Patient
    template_name = "patients/detail.html"    
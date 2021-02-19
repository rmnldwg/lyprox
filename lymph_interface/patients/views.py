from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def index(request):
    """Index view for the patients database/model."""
    return HttpResponse("Patients index.")
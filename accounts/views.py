from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.views import generic
from django.http import HttpResponse

from .forms import SignupRequestForm


def signup_request_view(request) -> HttpResponse:
    """Render form for requesting to be signed up as a user. Not yet 
    implemented."""
    if request.method == "POST":
        form = SignupRequestForm(request.POST)
        
        if form.is_valid():
            # TODO: Implement some sort of notification to notify the admin(s) 
            #   that a new request has been made and store the request data.
            pass
    
    else:
        form = SignupRequestForm()
        
    context = {"form": form}
    return render(request, "accounts/signup_request.html", context)
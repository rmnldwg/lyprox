from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views

from . import forms

class LoginView(auth_views.LoginView):
    form_class = forms.CustomAuthenticationForm
    template_name = "accounts/login.html"
    
    def get_success_url(self):
        return self.request.POST.get("next")
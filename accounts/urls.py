from django.urls import path
from django.contrib.auth import views as auth_views

from . import forms

app_name = "accounts"
urlpatterns = [
    path('login/',
         auth_views.LoginView.as_view(
             template_name="accounts/login.html",
             authentication_form=forms.CustomAuthenticationForm
         ),
         name='login'),
    path('logout/',
         auth_views.LogoutView.as_view(template_name="accounts/logout.html"),
         name='logout'),
]

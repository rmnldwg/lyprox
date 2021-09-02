from django.contrib.auth.forms import UsernameField, AuthenticationForm, UserCreationForm
from django.conf import settings
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Institution, User

class CustomAuthenticationForm(AuthenticationForm):
    username = UsernameField(
        widget=forms.TextInput(attrs={'autofocus': True, 
                                      "class": "input"})
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 
                                          "class": "input"}),
    )
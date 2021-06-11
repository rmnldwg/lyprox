from django.contrib.auth.forms import UsernameField, AuthenticationForm
from django.core.exceptions import ValidationError
from django import forms
from django.utils.translation import gettext, gettext_lazy as _


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

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.forms import widgets

from core.loggers import FormLoggerMixin

from .models import Institution, User


class CustomAuthenticationForm(AuthenticationForm):
    """Custom form that allows assignment of classes to widgets. Note that due
    to the inheritance from `AuthenticationForm` the email field, which is used
    to log in users, is called username.
    """
    username = UsernameField(
        label="Email address",
        widget=forms.TextInput(attrs={'autofocus': True,
                                      "class": "input"})
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password',
                                          "class": "input"}),
    )


class SignupRequestForm(forms.ModelForm):
    """Form for requesting to be signed up by an administrator."""
    class Meta:
        model = User
        fields = ["title", "first_name", "last_name", "email", "institution"]
        widgets = {
            "title": widgets.TextInput(attrs={"class": "input",
                                              "style": "width: 100px;"}),
            "first_name": widgets.TextInput(attrs={"class": "input"}),
            "last_name": widgets.TextInput(attrs={"class": "input"}),
            "email": widgets.EmailInput(attrs={"class": "input"}),
            "institution": widgets.TextInput(attrs={"class": "input"})
        }

    message = forms.CharField(
        label="Your message to us",
        widget=widgets.Textarea(
            attrs={"class": "textarea",
                   "placeholder": ("Why do you need this login, i.e. what data "
                                   "would you like to upload?"),
                   "rows": "5"})
    )

    def save(self, commit: bool):
        """Override save method, so that the entered data is not used to create
        a `User` instance, but the information is just stored/sent to an admin.
        """
        # TODO: Store the cleaned data somewhere or send it via email to the
        #   admin(s).

class InsitutionForm(FormLoggerMixin, forms.Form):
    """
    Form for creating an institution. This is not yet in use or even functional.
    """
    class Meta:
        model = Institution

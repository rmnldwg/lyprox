from django.contrib.auth.forms import UsernameField, AuthenticationForm, UserCreationForm
from django.conf import settings
from django import forms
from django.forms import widgets

from .models import Institution, User


class CustomAuthenticationForm(AuthenticationForm):
    """Custom form that allows assignment of classes to widgets. Note that due 
    to the inheritance from :class:`AuthenticationForm` the email field, which 
    is used to log in users, is called username.
    """
    #: The email address is used as a username field
    username = UsernameField(
        label="Email address",
        widget=forms.TextInput(attrs={'autofocus': True, 
                                      "class": "input"})
    )
    #: 
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 
                                          "class": "input"}),
    )


class SignupRequestForm(forms.ModelForm):
    """Form for requesting to be signed up by an administrator. Currentrly not 
    in use."""
    class Meta:
        """Meta class defining the user model and all the fields of interest."""
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
        a :class:`accounts.models.User` instance, but the information is just 
        stored/sent to an admin. Not implemented yet.
        """
        # TODO: Store the cleaned data somewhere or send it via email to the 
        #   admin(s).
        pass
"""
Defines the login and logout views for authenticating users. A sign-up views has not
been implemented yet.
"""
# pylint: disable=invalid-name

from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import CustomAuthenticationForm

app_name = "accounts"

login_view = auth_views.LoginView.as_view(
    template_name="accounts/login.html",
    authentication_form=CustomAuthenticationForm
)
logout_view = auth_views.LogoutView.as_view(
    template_name="accounts/logout.html"
)

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    # path('signup/', signup_request_view, name='signup_request')
]

from accounts.views import signup_request_view
from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm

from .forms import CustomAuthenticationForm
from .views import signup_request_view

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

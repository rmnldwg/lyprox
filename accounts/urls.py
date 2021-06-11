from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "accounts"
urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', 
         auth_views.LogoutView.as_view(template_name="accounts/logout.html"), 
         name='logout'),
]

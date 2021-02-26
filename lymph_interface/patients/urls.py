from django.urls import path

from . import views

app_name = "patients"
urlpatterns = [
    path("", views.ListView.as_view(), name="list"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("create/", views.create_patient, name="create"),
    path("<int:pk>/add/tumor/", views.add_tumor_to_patient, name="add_tumor"),
    path("<int:pk>/add/diagnose/", views.add_diagnose_to_patient, name="add_diagnose"),
]
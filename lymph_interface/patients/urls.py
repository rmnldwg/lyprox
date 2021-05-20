from django.urls import path
from django.views.generic.edit import UpdateView

from . import views

app_name = "patients"
urlpatterns = [
    path("", views.ListView.as_view(), name="list"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/update", views.UpdatePatientView.as_view(), name="update"),
    path("<int:pk>/delete", views.DeletePatientView.as_view(), name="delete"),
    path("create/", views.CreatePatientView.as_view(), name="create"),
    path("upload/", views.upload_patients, name="upload"),
    path("<int:pk>/tumor/add", views.add_tumor_to_patient, name="add_tumor"),
    path("<int:pk>/tumor/change", views.change_tumor_of_patient, name="change_tumor"),
    path("<int:pk>/diagnose/add", views.add_diagnose_to_patient, name="add_diagnose"),
    path("<int:pk>/diagnose/change", views.change_diagnose_of_patient, name="change_diagnose"),
    path("dashboard/", views.dashboard, name="dashboard"),
]

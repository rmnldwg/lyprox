from django.urls import path
from . import views

app_name = "patients"
urlpatterns = [
    path("", views.ListView.as_view(), name="list"),
    path("create/", views.CreatePatientView.as_view(), name="create"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/update", views.UpdatePatientView.as_view(), name="update"),
    path("<int:pk>/delete", views.DeletePatientView.as_view(), name="delete"),
    path("upload/", views.upload_patients, name="upload"),
    path("<int:pk>/tumor/create", views.CreateTumorView.as_view(), name="tumor_create"),
    path("<int:pk>/tumor/<int:tumor_pk>/update", views.UpdateTumorView.as_view(), name="tumor_update"),
    path("<int:pk>/tumor/<int:tumor_pk>/delete", views.DeleteTumorView.as_view(), name="tumor_delete"),
    path("<int:pk>/diagnose/add", views.add_diagnose_to_patient, name="add_diagnose"),
    path("<int:pk>/diagnose/change", views.change_diagnose_of_patient, name="change_diagnose"),
    path("dashboard/", views.dashboard, name="dashboard"),
]

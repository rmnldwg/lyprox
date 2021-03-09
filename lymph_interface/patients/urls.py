from django.urls import path

from . import views

app_name = "patients"
urlpatterns = [
    path("", views.ListView.as_view(), name="list"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("create/", views.create_patient, name="create"),
    path("upload/", views.upload_patients, name="upload"),
    path("<int:pk>/tumor/add", views.add_tumor_to_patient, name="add_tumor"),
    path("<int:pk>/diagnose/add", views.add_diagnose_to_patient, name="add_diagnose"),
    path("<int:pk>/tumor/delete", views.delete_tumor_from_patient, name="delete_tumor"),
    path("<int:pk>/diagnose/delete", views.delete_diagnose_from_patient, name="delete_diagnose"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
"""
Define the URLs that are available under ``https://lyprox.org/patients`` and which of
the `patients.views` should be called when they are requested.
"""
# pylint: disable=invalid-name

from django.urls import path

from . import views

app_name = "patients"
urlpatterns = [
    path(
        "",
        views.PatientListView.as_view(),
        name="list"
    ),
    path(
        "create/",
        views.CreatePatientView.as_view(),
        name="create"
    ),
    path(
        "<int:pk>/",
        views.PatientDetailView.as_view(),
        name="detail"
    ),
    path(
        "<int:pk>/update",
        views.UpdatePatientView.as_view(),
        name="update"
    ),
    path(
        "<int:pk>/delete",
        views.DeletePatientView.as_view(),
        name="delete"
    ),
    path(
        "<int:pk>/tumor/create",
        views.CreateTumorView.as_view(),
        name="tumor_create"
    ),
    path(
        "<int:pk>/tumor/<int:tumor_pk>/update",
        views.UpdateTumorView.as_view(),
        name="tumor_update"
    ),
    path(
        "<int:pk>/tumor/<int:tumor_pk>/delete",
        views.DeleteTumorView.as_view(),
        name="tumor_delete"
    ),
    path(
        "<int:pk>/diagnose/create",
        views.CreateDiagnoseView.as_view(),
        name="diagnose_create"
    ),
    path(
        "<int:pk>/diagnose/<int:diagnose_pk>/update",
        views.UpdateDiagnoseView.as_view(),
        name="diagnose_update"
    ),
    path(
        "<int:pk>/diagnose/<int:diagnose_pk>/delete",
        views.DeleteDiagnoseView.as_view(),
        name="diagnose_delete"
    ),
    path(
        "dataset/upload",
        views.CreateDatasetView.as_view(),
        name="dataset_upload"
    ),
    # path(                                    # this one is not yet implemented
    #     "dataset/create",
    #     views.CreateDatasetView.as_view(),
    #     name="dataset_create"
    # ),
    path(
        "dataset/",
        views.DatasetListView.as_view(),
        name="dataset_list"
    ),
    path(
        "dataset/<int:pk>/<str:which>",
        views.DatasetView.as_view(),
        name="dataset_download"
    ),
    path(
        "dataset/<int:pk>",
        views.DatasetView.as_view(),
        name="dataset_view"
    ),
]

"""
URLs related to the riskpredictor prediction app under ``https://lyprox.org/riskpredictor``. Like the
`dashboard`, this includes a dashboard and a help page.
"""
from django.urls import path

from .views import AddTrainedLymphModelView

app_name = "riskpredictor"
urlpatterns = [
    path("add/", AddTrainedLymphModelView.as_view(), name="add_model"),
    path("dashboard/", AddTrainedLymphModelView.as_view(), name="dashboard"),
]

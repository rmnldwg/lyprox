"""
URLs related to the riskpredictor prediction app under ``https://lyprox.org/riskpredictor``. Like the
`dashboard`, this includes a dashboard and a help page.
"""
from django.urls import path

from .views import (
    AddTrainedLymphModelView,
    ChooseTrainedLymphModelView,
    RiskPredictionView,
)

app_name = "riskpredictor"
urlpatterns = [
    path("add/", AddTrainedLymphModelView.as_view(), name="add"),
    path("list/", ChooseTrainedLymphModelView.as_view(), name="list"),
    path("<int:pk>/", RiskPredictionView.as_view(), name="dashboard"),
]

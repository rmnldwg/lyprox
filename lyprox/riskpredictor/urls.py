"""
URLs related to the riskpredictor prediction app under ``https://lyprox.org/riskpredictor``. Like the
`dashboard`, this includes a dashboard and a help page.
"""
from django.urls import path

from .views import (
    AddInferenceResultView,
    ChooseInferenceResultView,
    RiskPredictionView,
    riskpredictor_AJAX_view,
)

app_name = "riskpredictor"
urlpatterns = [
    path("add/", AddInferenceResultView.as_view(), name="add"),
    path("list/", ChooseInferenceResultView.as_view(), name="list"),
    path("<int:pk>/", RiskPredictionView.as_view(), name="dashboard"),
    path("<int:pk>/ajax/", riskpredictor_AJAX_view, name="ajax"),
]

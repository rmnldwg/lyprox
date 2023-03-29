"""
URLs related to the riskpredictor prediction app under ``https://lyprox.org/riskpredictor``. Like the
`dashboard`, this includes a dashboard and a help page.
"""
# pylint: disable=invalid-name

from django.urls import path

from . import views

app_name = "riskpredictor"
urlpatterns = [
    # path("", views.PredictionView.as_view(), name="prediction"),
    # path("ajax/", views.prediction_AJAX_view, name="ajax"),
    # path("help/", views.help_view, name="help")
]

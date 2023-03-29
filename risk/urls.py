"""
URLs related to the risk prediction app under ``https://lyprox.org/risk``. Like the
`dashboard`, this includes a dashboard and a help page.
"""
# pylint: disable=invalid-name

from django.urls import path

from . import views

app_name = "risk"
urlpatterns = [
    # path("", views.PredictionView.as_view(), name="prediction"),
    # path("ajax/", views.prediction_AJAX_view, name="ajax"),
    # path("help/", views.help_view, name="help")
]

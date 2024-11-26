"""
Define the two URLs within the dashboard app (reachable via
``https://lyprox.org/dashboard``). Those are the dashboard itself of course, but
also the help menu explaining how to use the former.
"""
# pylint: disable=invalid-name

from django.urls import path

from . import views

app_name = "dataexplorer"
urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("ajax/", views.dashboard_ajax_view, name="ajax"),
    path("help/", views.help_view, name="help")
]

"""
Define the URLs within the dashboard app.

It defines that the default dataexplorer view is handled by the `dashboard_view`
function and the AJAX view is handled by the `dashboard_ajax_view` function.

Also, a help page is defined here, which is handled by the `help_view` function.
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

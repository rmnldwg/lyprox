"""
Defines the URLs within the dashboard app.

This module's basic job is to define the `urlpatterns` list, which binds a URL (or a
part of a URL) to a view function. The view functions are defined in the `views` module.
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
"""
Contains three URL patterns:

1. The default URL pattern is an empty string (i.e.,
   ``https://lyprox.org/dataexplorer/``), which is handled by the `dashboard_view`.
2. The AJAX URL pattern is ``/ajax/``, which is handled by the `dashboard_ajax_view`.
3. The help URL pattern is ``/help/``, which is handled by the `help_view`.
"""

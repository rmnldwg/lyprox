"""Defines the URLs within the dashboard app.

This module's basic job is to define the `urlpatterns` list, which binds a URL (or a
part of a URL) to a view function. The view functions are defined in the `views` module.
"""

from django.urls import path

from lyprox.dataexplorer import views

app_name = "dataexplorer"
urlpatterns = [
    path("", views.render_data_stats, name="dashboard"),
    path("ajax/", views.update_data_stats, name="ajax"),
    path("help/", views.help_view, name="help"),
]
"""
Contains three URL patterns:

1. The default URL pattern is an empty string (i.e.,
   ``https://lyprox.org/dataexplorer/``), which is handled by the `render_data_stats`.
2. The AJAX URL pattern is ``/ajax/``, which is handled by the `update_data_stats`.
3. The help URL pattern is ``/help/``, which is handled by the `help_view`.
"""

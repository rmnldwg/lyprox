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
    path("table/", views.render_data_table, name="table"),
    path("download/", views.make_csv_download, name="download"),
    path("help/", views.help_view, name="help"),
]
"""
Contains four URL patterns:

1. The default URL pattern is an empty string (i.e.,
   ``https://lyprox.org/dataexplorer/``), which is handled by the `render_data_stats`.
   It is called when the user initially navigates to the dashboard site. But also when
   a GET request is sent (e.g. by pressing Alt+C) instead of the POST request (see
   the AJAX URL pattern below).
2. The AJAX URL pattern is ``/ajax/``, which is handled by the `update_data_stats`.
   Its job is to update the already rendered HTML dashboard with new statistics, when
   the user updates their selection and clicks the "Compute" button. This sends a POST
   request to the server.
3. The table URL pattern is ``/table/``, which is handled by the `render_data_table`.
   It displays a (possibly filtered) `pandas.DataFrame` as HTML.
4. The help URL pattern is ``/help/``, which is handled by the `help_view`.
"""

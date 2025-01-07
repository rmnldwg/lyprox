"""
Orchestrate the logic of the dashboard.

The views in this module are being called when the user sends a request to the server.
Which view is called for which URL is defined in the `urls` module. The views process
the data in the request and return a response. In between, the views delegate the
creation of the `DashboardForm`, its validation and cleaning, then `execute_query` and
compute the `Statistics` from the filtered dataset.

The way this typically plays out in detail is the following: The user navigates to the
URL ``https://lyprox.org/dataexplorer/`` and the `dashboard_view` is called. This view
creates an instance of `DashboardForm.from_initial` with the default values and renders
the dashboard HTML layout. The template that is used for this is defined in
``./lyprox/dataexplorer/templates/dataexplorer/layout.html``. The user can then
interact with the dashboard and change the values of the form fields. Upon clicking the
"Compute" button, an AJAX request is sent with the updated form data. In the
`dashboard_ajax_view`, another `DashboardForm` instance is created, this time with the
selected queries from the user. The form is validated and cleaned (using
``form.is_valid()``) and the cleaned data (``form.cleaned_data``) is passed to the
`execute_query` function. This function queries the dataset and returns the patients
that match the query.

From the returned queried patients, the `Statistics` class is used to compute the
statistics, which are then returned as JSON data to the frontend. The frontend then
updates the dashboard with the new statistics without reloading the entire page.

Read more about how views work in Django, what responses they return and how to use
the context they may provide in the `Django documentation`_.

.. _Django documentation: https://docs.djangoproject.com/en/4.2/topics/http/views/
"""
import json
import logging

from django.http import HttpResponseBadRequest
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
from lydata.utils import get_default_modalities

from lyprox.dataexplorer.forms import DashboardForm
from lyprox.dataexplorer.query import Statistics, execute_query

logger = logging.getLogger(__name__)


def help_view(request) -> HttpResponse:
    """Simply display the dashboard help text."""
    template_name = "dataexplorer/help/index.html"
    context = {"modalities": get_default_modalities()}
    return render(request, template_name, context)


def dashboard_view(request):
    """
    Return the dashboard view when the user first accesses the dashboard.

    This view handles GET requests, which typically only occur when the user first
    navigates to the dashboard. But it is also possible to query the dashboard with
    URL parameters (e.g. ``https://lyprox.org/dataexplorer/?t_stage=1&t_stage=2...``).

    The view creates a `DashboardForm` instance with the data from a GET request or
    with the default initial values. It then calls `execute_query` with
    ``form.cleaned_data`` and returns the `Statistics.from_dataset()` using the queried
    dataset to the frontend.
    """
    request_data = request.GET
    form = DashboardForm(request_data, user=request.user)

    if not form.is_valid():
        logger.info("Dashboard form not valid.")
        form = DashboardForm.from_initial(user=request.user)

    if not form.is_valid():
        logger.error("Form is not valid even after initializing with initial data.")
        return HttpResponseBadRequest("Form is not valid.")

    patients = execute_query(cleaned_form=form.cleaned_data)

    context = {
        "form": form,
        "modalities": get_default_modalities(),
        "stats": Statistics.from_dataset(patients),
    }

    return render(request, "dataexplorer/layout.html", context)


def dashboard_ajax_view(request):
    """
    AJAX view to update the dashboard statistics without reloading the page.

    This view is conceptually similar to the `dashboard_view`, but instead of rendering
    the entire HTML page, it returns only a JSON response with the updated statistics
    which are then handled by some JavaScript on the frontend.

    It also doesn't receive a GET request, but a POST request with the `DashboardForm`
    fields as JSON data. The form is validated and cleaned as always (using
    ``form.is_valid()``).

    Some resources to learn more about AJAX requests in Django can be found
    `in this article`_.

    .. _in this article: https://realpython.com/django-and-ajax-form-submissions/
    """
    request_data = json.loads(request.body.decode("utf-8"))
    form = DashboardForm(request_data, user=request.user)

    if not form.is_valid():
        logger.error("Form is not valid even after initializing with initial data.")
        return JsonResponse(data={"error": "Something went wrong."}, status=400)

    patients = execute_query(cleaned_form=form.cleaned_data)
    stats = Statistics.from_dataset(patients).model_dump()
    stats["type"] = "stats"
    return JsonResponse(data=stats)

"""
This module defines a ``django_filters.FilterSet`` based class that allows
relatively easy filtering and sorting of models. In our case, we have
implemented only a ``PatientFilter`` for the ``views.PatientListView`` which
almost automatically provides a form that can be passed and used in the HTML
template of the list view.

By using third-party app ``django_filters`` (`docs`_) we can define by what
fields we want to filter/sort our models and how.

.. _docs: https://django-filter.readthedocs.io/en/stable/
"""
import logging

import django_filters
from django.forms import widgets

from .models import Dataset, Patient

logger = logging.getLogger(__name__)


def public_or_logged_in(request):
    """
    Return a queryset of datasets, depending on whether a user is logged in or not.
    """
    public_datasets = Dataset.objects.all().filter(is_public=True)

    if request is None:
        return public_datasets

    if request.user.is_authenticated:
        return Dataset.objects.all()

    return public_datasets


class PatientFilter(django_filters.FilterSet):
    """
    A ``django_filters.FilterSet`` which allows for easy filtering of a
    patient queryset for any fields defined here.
    """
    class Meta:
        """Define which django model this should act on."""
        model = Patient
        fields = ["diagnose_date", "gender", "age",
                  "t_stage", "n_stage", "m_stage"]

    diagnose_date = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={"class": "input",
                                                         "type": "date"})
    )
    gender = django_filters.ChoiceFilter(
        choices=(("male", "male"), ("female", "female")),
        empty_label="both",
        widget=widgets.Select(attrs={"class": "select"})
    )
    age = django_filters.RangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={"class": "input",
                                                         "type": "text"})
    )
    tumor__t_stage = django_filters.MultipleChoiceFilter(
        choices=Patient.T_stages.choices,
        widget=widgets.SelectMultiple()
    )
    n_stage = django_filters.MultipleChoiceFilter(
        choices=Patient.N_stages.choices,
        widget=widgets.SelectMultiple()
    )
    m_stage = django_filters.MultipleChoiceFilter(
        choices=Patient.M_stages.choices,
        widget=widgets.SelectMultiple()
    )
    dataset = django_filters.ModelMultipleChoiceFilter(
        queryset=public_or_logged_in,
    )

    # additional form field for sorting
    ordering = django_filters.OrderingFilter(
        fields=[
            ("diagnose_date", "diagnose_date"),
            ("age", "age"),
            ("t_stage", "t_stage")
        ],
        field_labels={
            "diagnose_date": "Diagnose date",
            "age": "Age",
            "t_stage": "T-stage"
        }
    )

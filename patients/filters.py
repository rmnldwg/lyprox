from accounts.models import Institution
from django.forms import widgets
import django_filters

from .models import Patient


class PatientFilter(django_filters.FilterSet):
    """Class to define what widgets to use for filtering a given class."""
    diagnose_date = django_filters.DateFromToRangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={"class": "input",
                                                         "type": "date"})
    )  #:
    gender = django_filters.ChoiceFilter(
        choices=(("male", "male"), ("female", "female")),
        empty_label="both",
        widget=widgets.Select(attrs={"class": "select"})
    )  #:
    age = django_filters.RangeFilter(
        widget=django_filters.widgets.RangeWidget(attrs={"class": "input",
                                                         "type": "text"})
    )  #:
    tumor__t_stage = django_filters.MultipleChoiceFilter(
        choices=Patient.T_stages.choices,
        widget=widgets.SelectMultiple()
    )  #:
    n_stage = django_filters.MultipleChoiceFilter(
        choices=Patient.N_stages.choices,
        widget=widgets.SelectMultiple()
    )  #:
    m_stage = django_filters.MultipleChoiceFilter(
        choices=Patient.M_stages.choices,
        widget=widgets.SelectMultiple()
    )  #:
    institution = django_filters.ModelMultipleChoiceFilter(
        queryset=Institution.objects.all()
    )  #:
    
    #: Additional form fields for choosing by what to sort
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
    
    class Meta:
        """Defining the ``Meta`` class of this filter."""
        model = Patient
        #: List of fields that will be filterable
        fields = ["diagnose_date", "gender", "age", 
                  "t_stage", "n_stage", "m_stage",
                  "institution"]

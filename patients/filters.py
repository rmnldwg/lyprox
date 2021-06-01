from django.forms import widgets
import django_filters

from .models import Patient, Tumor, Diagnose, T_STAGES, N_STAGES, M_STAGES


class PatientFilter(django_filters.FilterSet):
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
        choices=T_STAGES,
        widget=widgets.SelectMultiple()
    )
    n_stage = django_filters.MultipleChoiceFilter(
        choices=N_STAGES,
        widget=widgets.SelectMultiple()
    )
    m_stage = django_filters.MultipleChoiceFilter(
        choices=M_STAGES,
        widget=widgets.SelectMultiple()
    )
    
    class Meta:
        model = Patient
        fields = ["diagnose_date", "gender", "age", 
                  "tumor__t_stage", "n_stage", "m_stage"]

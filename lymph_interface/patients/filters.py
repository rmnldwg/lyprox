from .models import Patient, Tumor, Diagnose

import django_filters


class PatientFilter(django_filters.FilterSet):
    class Meta:
        model = Patient
        fields = {
            "age": ["lt", "gt"],
            "diagnose_date": ["year__lte", "year__gte"],
            "tumor__t_stage": ["gt", "lt"],
        }
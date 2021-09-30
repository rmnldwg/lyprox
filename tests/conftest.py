import pytest

from pytest_factoryboy import register

from factories import (InstitutionFactory, UserFactory, 
                       PatientFactory, TumorFactory, DiagnoseFactory)

register(UserFactory)
register(InstitutionFactory)
register(PatientFactory)
register(TumorFactory)
register(DiagnoseFactory)
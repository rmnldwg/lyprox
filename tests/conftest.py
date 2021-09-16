import pytest

from pytest_factoryboy import register

from factories import InstitutionFactory, UserFactory, PatientFactory

register(UserFactory)
register(InstitutionFactory)
register(PatientFactory)
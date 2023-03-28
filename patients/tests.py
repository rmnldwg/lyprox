"""Testing the core models' functionality."""

from django.forms import ValidationError
from django.test import TestCase

from accounts.models import Institution
from patients.models import Dataset, Patient


class PatientTestCase(TestCase):
    """Test the `models.Patient`."""
    def setUp(self) -> None:
        return super().setUp()

    def test_whatever(self):
        num_institutions = Institution.objects.all().count()
        self.assertEqual(num_institutions, 3)

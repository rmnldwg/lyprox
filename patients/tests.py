"""Testing the core models' functionality."""

from django.forms import ValidationError
from django.test import TestCase

from accounts.models import Institution
from patients.models import Dataset, Patient


class PatientTestCase(TestCase):
    """Test the `models.Patient`."""

    def test_whatever(self):
        institution = Institution.objects.create(
            name="TestClinic", shortname="TC", country="Testland",
        )
        dataset = Dataset.objects.create(name="TestSet", institution=institution)

        create_patient = lambda: Patient.objects.create(
            sex="female", age=42, diagnose_date="2023-03-24", dataset=dataset,
        )
        create_patient()

        self.assertRaises(ValidationError, create_patient)

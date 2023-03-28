"""Testing the core models' functionality."""
# pylint: disable=no-member

from pathlib import Path
import random

import pandas as pd
from pandas import testing

from django.core.files import File
from django.test import TestCase

from core.settings import BASE_DIR
from accounts.models import Institution
from patients.models import Dataset, Diagnose, Patient, Tumor, DuplicateFileError, LockedDatasetError


class DatasetTestCase(TestCase):
    """Test the `models.Dataset`."""
    def setUp(self) -> None:
        self.test_file_path = f"{BASE_DIR}/patients/test.csv"
        self.dset = self.create_dataset()
        return super().setUp()


    def create_dataset(self):
        with open(self.test_file_path, mode="rb") as file:
            file = File(file)
            dset = Dataset.objects.create(
                name="test",
                description="Does the import of a CSV file work?",
                institution=Institution.objects.get(shortname="USZ"),
                source_csv=file,
            )
            dset.import_source_csv_to_db()
            self.source_file_path = Path(dset.source_csv.path)

        return dset


    def test_unique_file_constraint(self):
        """Make sure a file cannot be uploaded twice."""
        self.assertRaises(DuplicateFileError, self.create_dataset)


    def test_dataset_lock(self):
        """Check that a locked dataset cannot be modified."""
        patients = list(Patient.objects.filter(dataset=self.dset))
        rand_patient = random.choice(patients)

        tumors = list(Tumor.objects.filter(patient__dataset=self.dset))
        rand_tumor = random.choice(tumors)

        diagnoses = list(Diagnose.objects.filter(patient__dataset=self.dset))
        rand_diagnose = random.choice(diagnoses)

        self.assertTrue(self.dset.is_locked)
        self.assertRaises(LockedDatasetError, self.dset.delete)
        self.assertRaises(LockedDatasetError, rand_patient.delete)
        self.assertRaises(LockedDatasetError, rand_tumor.delete)
        self.assertRaises(LockedDatasetError, rand_diagnose.delete)


    def test_ioports(self):
        """Test if im- and export preserve data."""
        compare_cols = ["sex", "age", "alcohol_abuse", "nicotine_abuse", "hpv_status"]

        test_table = pd.read_csv(self.test_file_path, header=[0,1,2])
        test_table = test_table["patient", "#"][compare_cols]

        export_table = self.dset.get_pandas_from_db()
        export_table = export_table["patient", "#"][compare_cols]

        pd.testing.assert_frame_equal(test_table, export_table, check_dtype=False)


    def tearDown(self) -> None:
        self.source_file_path.unlink()
        return super().tearDown()

"""
Unit test for the `query` module.
"""
from django.test import TestCase

from . import new_query


class QueryTests(TestCase):
    """Run unit test for the `new_query` module."""
    def test_extract_filter_pattern(self):
        """Make sure all LNLs are extracted and correctly placed in dictionary."""
        kwargs = {
            "ipsi_I": True,
            "contra_VII": False,
            "ipsi_Va": None,
        }
        filter_pattern = new_query.extract_filter_pattern(kwargs)
        self.assertDictEqual(
            d1 = filter_pattern,
            d2 = {
                "ipsi": {"I": True, "Va": None},
                "contra": {"VII": False},
            },
        )

    def test_ModalityCombinor(self):
        """Test the helper class `new_query.ModalityCombinor`."""
        for method in ["maxLLH", "rank"]:
            combinor = new_query.ModalityCombinor(method)

            none_tuple = (None , None , None , None , None , None , None )
            true_tuple = (True , True , True , None , None , None , None )
            path_tuple = (False, False, False, False, False, True , False)

            none_combined = combinor.combine(none_tuple)
            true_combined = combinor.combine(true_tuple)
            path_combined = combinor.combine(path_tuple)

            self.assertIsNone(none_combined)
            self.assertTrue(true_combined)
            self.assertTrue(path_combined)

"""Test the querying functionality."""

import pandas as pd
from pytest import fixture

from lyprox.dataexplorer.loader import DataInterface
from lyprox.dataexplorer.query import BaseStatistics, Statistics


@fixture
def dataset(data_interface: DataInterface) -> pd.DataFrame:
    """Return a dataset."""
    return data_interface.get_dataset()


def test_stats_from_datasets(dataset: pd.DataFrame) -> None:
    """Test the statistics computed from a dataset."""
    stats = BaseStatistics.from_datasets(dataset)
    assert stats.total == 1255, "Wrong total number of patients"
    assert stats.hpv == {True: 582, False: 378, None: 295}, "Wrong HPV counts"


def test_lnl_stats(dataset: pd.DataFrame) -> None:
    """Test the statistics computed from the LNLS dataset."""
    stats = Statistics.from_datasets(dataset)
    assert stats.ipsi_II == {True: 671, False: 541, None: 43}, "Wrong ipsi_II counts"

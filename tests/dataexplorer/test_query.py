"""Test the querying functionality."""

from lydata import C
import pandas as pd
from pytest import fixture

from lyprox.dataexplorer.loader import DataInterface
from lyprox.dataexplorer.query import BaseStatistics, Statistics


@fixture
def dataset(data_interface: DataInterface) -> pd.DataFrame:
    """Return a dataset."""
    return data_interface.get_dataset()


def test_contradiction(dataset: pd.DataFrame) -> None:
    """Test that one (previously present) contradiction is not in the dataset."""
    is_iII_healthy = C("max_llh", "ipsi", "II") == False
    is_iIIa_involved = C("max_llh", "ipsi", "IIa") == True
    contradiction = is_iII_healthy & is_iIIa_involved
    assert dataset.ly.query(contradiction).empty


def test_stats_from_datasets(dataset: pd.DataFrame) -> None:
    """Test the statistics computed from a dataset."""
    stats = BaseStatistics.from_datasets(dataset)
    assert stats.total == 1255, "Wrong total number of patients"
    assert stats.hpv == {True: 582, False: 378, None: 295}, "Wrong HPV counts"


def test_lnl_stats(dataset: pd.DataFrame) -> None:
    """Test the statistics computed from the LNLS dataset."""
    stats = Statistics.from_datasets(dataset)
    assert stats.ipsi_II == {True: 696, False: 559, None: 0}, "Wrong ipsi_II counts"

"""Test the querying functionality."""

import pandas as pd
from pytest import fixture

from lyprox.dataexplorer.loader import DataInterface
from lyprox.dataexplorer.query import BaseStatistics


@fixture
def dataset() -> pd.DataFrame:
    """Return a dataset."""
    return DataInterface().get_dataset()


def test_stats_from_datasets(dataset: pd.DataFrame) -> None:
    """Test the statistics computed from a dataset."""
    stats = BaseStatistics.from_datasets(dataset)
    assert stats.total == 287

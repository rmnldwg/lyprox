"""Test the querying functionality."""

from typing import Any

import pandas as pd
from lydata import C

from lyprox.dataexplorer.query import BaseStatistics, Statistics, execute_query


def test_contradiction(dataset: pd.DataFrame) -> None:
    """Test that one (previously present) contradiction is not in the dataset."""
    is_iII_healthy = C("max_llh", "ipsi", "II") == False
    is_iIIa_involved = C("max_llh", "ipsi", "IIa") == True
    contradiction = is_iII_healthy & is_iIIa_involved
    assert dataset.ly.query(contradiction).empty


def test_stats_from_datasets(dataset: pd.DataFrame) -> None:
    """Test the statistics computed from a dataset."""
    stats = BaseStatistics.from_table(dataset)
    assert stats.total == 1255, "Wrong total number of patients"
    assert stats.hpv == {True: 582, False: 378, None: 295}, "Wrong HPV counts"


def test_lnl_stats(dataset: pd.DataFrame) -> None:
    """Test the statistics computed from the LNLS dataset."""
    stats = Statistics.from_table(dataset)
    assert stats.ipsi_II == {True: 696, False: 559, None: 0}, "Wrong ipsi_II counts"


def test_execute_query(cleaned_initial_form: dict[str, Any]) -> None:
    """Test the execution of a query."""
    queried_dataset = execute_query(cleaned_form_data=cleaned_initial_form)
    assert len(queried_dataset) == 1254, "Wrong number of patients in queried dataset"

    cleaned_initial_form["ipsi_II"] = True
    cleaned_initial_form["contra_II"] = False
    queried_dataset = execute_query(cleaned_form_data=cleaned_initial_form)
    assert len(queried_dataset) == 696, "Wrong number of patients in queried dataset"

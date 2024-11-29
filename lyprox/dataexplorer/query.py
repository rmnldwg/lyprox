"""Executes the query sent by the user via the dashboard form and returns statistics."""

import logging
from typing import Any, Literal, TypeVar

import lydata  # noqa: F401
import numpy as np
import pandas as pd
from pydantic import BaseModel, create_model

from lyprox.dataexplorer.loader import DataInterface  # noqa: F401
from lyprox.settings import LNLS

logger = logging.getLogger(__name__)


def safe_value_counts(column: pd.Series) -> dict[Any, int]:
    """
    Return the value counts of a column, including missing values as `None`.

    >>> column = pd.Series(['a', 'b', 'c', np.nan, 'a', 'b', 'c', 'a', 'b', 'c'])
    >>> safe_value_counts(column)
    {'a': 3, 'b': 3, 'c': 3, None: 1}
    """
    result = {}

    for key, value in column.value_counts(dropna=False).to_dict().items():
        key = key if not pd.isna(key) else None
        result[key] = value

    return result


T = TypeVar("T", bound="BaseStatistics")

class BaseStatistics(BaseModel):
    """Basic statistics to be computed and displayed on the dashboard."""
    datasets: dict[str, int]
    sex: dict[Literal["male", "female"], int]
    smoke: dict[Literal[True, False, None], int]
    hpv: dict[Literal[True, False, None], int]
    surgery: dict[Literal[True, False, None], int]
    t_stage: dict[Literal[0,1,2,3,4], int]
    n_stage: dict[Literal[0,1,2,3], int]
    subsite: dict[str, int]
    central: dict[Literal[True, False, None], int]
    midext: dict[Literal[True, False, None], int]

    @property
    def total(self) -> int:
        """Return the total number of patients in the dataset."""
        return sum(self.datasets.values())

    @classmethod
    def from_datasets(cls: type[T], dataset: pd.DataFrame) -> T:
        """
        Compute statistics from a dataset.

        >>> di = DataInterface()
        >>> di.load_and_enhance_datasets(year=2021, institution="usz")
        >>> dataset = di.get_dataset()
        >>> stats = BaseStatistics.from_datasets(dataset)
        >>> stats.hpv
        {True: 181, False: 96, None: 10}
        """
        stats = {}
        for name in cls.model_fields:
            # key `datasets` is not a shorthand code provided by the `lydata` package
            if name == "datasets":
                stats[name] = safe_value_counts(dataset["dataset", "info", "name"])
                continue

            # key `central` is not a shorthand code provided by the `lydata` package
            if name == "central":
                stats[name] = safe_value_counts(dataset["tumor", "1", "central"])
                continue

            stats[name] = safe_value_counts(dataset.ly[name])

        return cls(**stats)


lnl_fields = {
    f"{side}_{lnl}": (dict[Literal[True, False, None], int], ...)
    for side in ["ipsi", "contra"]
    for lnl in LNLS
}


Statistics = create_model(
    "Statistics",
    __base__=BaseStatistics,
    __doc__="Statistics to be computed and displayed on the dashboard.",
    **lnl_fields,
)

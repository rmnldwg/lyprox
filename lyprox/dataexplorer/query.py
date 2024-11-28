"""Executes the query sent by the user via the dashboard form and returns statistics."""

import logging
from typing import Literal, TypeVar

import lydata  # noqa: F401
import numpy as np
import pandas as pd
from pydantic import BaseModel, create_model

from lyprox.dataexplorer.loader import DataInterface  # noqa: F401
from lyprox.settings import LNLS

logger = logging.getLogger(__name__)


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
    def from_datasets(cls: type[T], datasets: dict[str, pd.DataFrame]) -> T:
        """
        Compute statistics from a dataset.

        >>> datasets = DataInterface().get_datasets(visibility="public")
        >>> stats = BaseStatistics.from_datasets(datasets)
        >>> print(stats)
        """
        dataset = pd.concat(
            list(datasets.values()),
            axis="index",
            ignore_index=True,
        )

        stats = {}
        for name in cls.model_fields:
            # the key `datasets` is not a columns in the dataset
            if name == "datasets":
                stats[name] = {n: len(df) for n, df in datasets.items()}
                continue

            # the key `central` is not a shorthand code provided by the `lydata` package
            if name == "central":
                stats[name] = (
                    dataset["tumor", "1", "central"]
                    .value_counts(dropna=False)
                    .to_dict()
                )
                stats[name][None] = stats[name].pop(np.nan, 0)
                continue

            stats[name] = (
                getattr(dataset.ly, name)
                .value_counts(dropna=False)
                .to_dict()
            )
            stats[name][None] = stats[name].pop(np.nan, 0)

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

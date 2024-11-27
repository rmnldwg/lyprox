"""Executes the query sent by the user via the dashboard form and returns statistics."""

import logging
from typing import Literal

import lydata  # noqa: F401
import pandas as pd
import pandera as pa
from pydantic import BaseModel, create_model

from lyprox.dataexplorer.loader import DataInterface
from lyprox.settings import LNLS

logger = logging.getLogger(__name__)


class BaseStatistics(BaseModel):
    """Basic statistics to be computed and displayed on the dashboard."""
    datasets: dict[str, int]
    sex: dict[Literal["male", "female"], int]
    nicotine_abuse: dict[Literal[True, False, None], int]
    hpv_status: dict[Literal[True, False, None], int]
    neck_dissection: dict[Literal[True, False, None], int]
    n_status: dict[Literal[0,1,2,3], int]
    subsites: pd.Series
    t_stages: pd.Series
    central: dict[Literal[True, False, None], int]
    extension: dict[Literal[True, False, None], int]

    @property
    def total(self) -> int:
        """Return the total number of patients in the dataset."""
        return sum(self.datasets.values())


lnl_fields = {
    f"{side}_{lnl}": pd.Series
    for side in ["ipsi", "contra"]
    for lnl in LNLS
}


Statistics = create_model(
    model_name="Statistics",
    __base__=BaseStatistics,
    __doc__="Statistics to be computed and displayed on the dashboard.",
    **lnl_fields,
)

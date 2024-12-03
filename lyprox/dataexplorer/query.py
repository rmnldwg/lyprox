"""Executes the query sent by the user via the dashboard form and returns statistics."""

import logging
from typing import Annotated, Any, Callable, Literal, TypeVar

import lydata  # noqa: F401
import lydata.utils as lyutils
import numpy as np
import pandas as pd
from pydantic import AfterValidator, BaseModel, create_model

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


KT = TypeVar("KT")
EnsureKeysSignature = Callable[[dict[KT, int]], dict[KT, int]]

def make_ensure_keys_validator(keys: list[KT]) -> EnsureKeysSignature:
    """
    Create an `AfterValidator` to ensure all `keys` are present in the data.

    This creates a function that can be used with pydantic's `AfterValidator` to ensure
    that all `keys` are present in the validated data. pydantic first receives the value
    counts from the `safe_value_counts` function, validates it, and then calls the
    function created by this wrapper to ensure that all keys are present.
    """
    def ensure_keys(data: dict[KT, int]) -> dict[KT, int]:
        """Ensure all `keys` are present in the data."""
        initial = {key: 0 for key in keys}
        initial.update(data)
        return initial

    return ensure_keys

NullableBoolCounts = Annotated[
    dict[Literal[True, False, None], int],
    AfterValidator(make_ensure_keys_validator([True, False, None])),
]
SexCounts = Annotated[
    dict[Literal["male", "female"], int],
    AfterValidator(make_ensure_keys_validator(keys=["male", "female"])),
]
TStageCounts = Annotated[
    dict[Literal[0, 1, 2, 3, 4], int],
    AfterValidator(make_ensure_keys_validator(keys=[0, 1, 2, 3, 4])),
]
NStageCounts = Annotated[
    dict[Literal[0, 1, 2, 3], int],
    AfterValidator(make_ensure_keys_validator(keys=[0, 1, 2, 3])),
]

T = TypeVar("T", bound="BaseStatistics")

class BaseStatistics(BaseModel):
    """Basic statistics to be computed and displayed on the dashboard."""
    datasets: dict[str, int]
    sex: SexCounts
    smoke: NullableBoolCounts
    hpv: NullableBoolCounts
    surgery: NullableBoolCounts
    t_stage: TStageCounts
    n_stage: NStageCounts
    subsite: dict[str, int]
    central: NullableBoolCounts
    midext: NullableBoolCounts

    @property
    def total(self) -> int:
        """Return the total number of patients in the dataset."""
        return sum(self.datasets.values())

    @classmethod
    def from_datasets(
        cls: type[T],
        dataset: pd.DataFrame,
        modalities: dict[str, lyutils.ModalityConfig] | None = None,
        method: Literal["max_llh", "rank"] = "max_llh",
    ) -> T:
        """
        Compute statistics from a dataset.

        >>> di = DataInterface()
        >>> di.load_and_enhance_datasets(year=2021, institution="usz")
        >>> dataset = di.get_dataset()
        >>> stats = BaseStatistics.from_datasets(dataset)
        >>> stats.hpv
        {True: 181, False: 96, None: 10}
        """
        combined = dataset.ly.combine(modalities=modalities, method=method)
        stats = {}
        for name in cls.model_fields:
            # these fields deal with the LNLs
            if "ipsi" in name or "contra" in name:
                side, lnl = name.split("_")
                stats[name] = safe_value_counts(combined[side, lnl])
                continue

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
    f"{side}_{lnl}": (NullableBoolCounts, ...)
    for side in ["ipsi", "contra"]
    for lnl in LNLS
}


Statistics = create_model(
    "Statistics",
    __base__=BaseStatistics,
    __doc__="""
    Statistics to be computed and displayed on the dashboard.

    This class extends the `BaseStatistics` class by adding the dynamically created
    fields for the LNLs. That way, I did not have to write them by hand.
    """,
    **lnl_fields,
)

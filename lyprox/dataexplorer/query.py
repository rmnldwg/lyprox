"""
Querying and generating statistics from the dataset.

In this module, we define the classes and methods to filter and query the datasets, as
well as compute statistics from a queried/filtered dataset to be displayed on the
main dashboard of LyProX.
"""
import logging
import time
from collections.abc import Callable
from typing import Annotated, Any, Literal, TypeVar

import lydata  # noqa: F401
import lydata.accessor
import lydata.utils as lyutils
import pandas as pd
from lydata import C
from pydantic import AfterValidator, BaseModel, computed_field, create_model

from lyprox.dataexplorer.loader import DataInterface  # noqa: F401
from lyprox.settings import LNLS

logger = logging.getLogger(__name__)


def execute_query(
    cleaned_form: dict[str, Any],
    dataset: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Execute a query on a dataset.

    After validating a `DashboardForm` by calling ``form.is_valid()``, the cleaned data
    is accessible as the attribute ``form.cleaned_data``. The returned dictionary should
    be passed to this function as the ``cleaned_form`` argument. Based on this cleaned
    form data, a query is executed on the dataset and the resulting dataset is returned.

    If no dataset is provided, the default dataset is loaded from the `DataInterface`.
    """
    start_time = time.perf_counter()
    dataset = dataset or DataInterface().get_dataset()

    modalities = {
        name: modality_config
        for name, modality_config in lyutils.get_default_modalities().items()
        if name in cleaned_form["modalities"]
    }
    method = cleaned_form["modality_combine"]
    dataset[method] = dataset.ly.combine(
        modalities=modalities,
        method=method,
    )

    query = C("dataset", "info", "name").isin(cleaned_form["datasets"])
    query &= C("t_stage").isin(cleaned_form["t_stage"])
    query &= C("subsite").isin(cleaned_form["subsite"])

    for short_names in ["smoke", "hpv", "surgery", "midext", "central"]:
        if cleaned_form[short_names] is not None:
            query &= C(short_names) == cleaned_form[short_names]

    if (is_n_plus := cleaned_form["is_n_plus"]) is not None:
        query &= C("n_stage") > 0 if is_n_plus else C("n_stage") == 0

    for side in ["ipsi", "contra"]:
        for lnl in LNLS:
            field = f"{side}_{lnl}"
            if (value := cleaned_form[field]) is not None:
                query &= C(method, side, lnl) == value

    queried_dataset = dataset.ly.query(query)
    end_time = time.perf_counter()

    logger.debug(f"Query: {query}")
    logger.info(f"Query executed in {end_time - start_time:.2f} seconds.")
    logger.info(f"{len(queried_dataset)} patients remain in queried dataset.")

    return queried_dataset


def safe_value_counts(column: pd.Series) -> dict[Any, int]:
    """
    Return the value counts of a column, including missing values as ``None``.

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
    Create an `AfterValidator` to ensure all ``keys`` are present in the data.

    This creates a function that can be used with pydantic's `AfterValidator` to ensure
    that all ``keys`` are present in the validated data. pydantic first receives the
    value counts from the `safe_value_counts` function, validates it, and then calls the
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
IsNPlusCounts = Annotated[
    dict[Literal[True, False, None], int],
    AfterValidator(make_ensure_keys_validator(keys=[True, False, None])),
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
    is_n_plus: IsNPlusCounts
    subsite: dict[str, int]
    central: NullableBoolCounts
    midext: NullableBoolCounts

    @computed_field
    @property
    def total(self) -> int:
        """Return the total number of patients in the dataset."""
        return sum(self.datasets.values())

    @classmethod
    def from_dataset(
        cls: type[T],
        dataset: pd.DataFrame,
        modalities: dict[str, lyutils.ModalityConfig] | None = None,
        method: Literal["max_llh", "rank"] = "max_llh",
    ) -> T:
        """
        Compute statistics from a dataset.

        This method computes e.g. how many patients in the queried dataset are
        HPV positive, or how many patients have a certain T-stage. The statistics are
        computed from the queried dataset and passed to the context of the
        `dataexplorer.views`. From there, the statistics can be displayed in the
        rendered HTML or JSON response.

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

            # key `is_n_plus` is not a shorthand code provided by the `lydata` package
            if name == "is_n_plus":
                stats[name] = safe_value_counts(dataset.ly["n_stage"] > 0)
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

    The intended use is to first query a dataset using the `execute_query` function
    with the cleaned form data from the `DashboardForm`. Then, pass the queried dataset
    to this class's `from_dataset` method to compute the statistics. Finally, pass the
    computed statistics to the context of the `dataexplorer.views` to be displayed in
    the rendered HTML or JSON response.

    By design, this class's fields mirror the fields of the `DashboardForm` class. This
    is obviously necessary, since any information data might be queried on is also
    information that one can compute statistics on.
    """,
    **lnl_fields,
)

"""
Querying and generating statistics from the dataset.

In this module, we define the classes and methods to filter and query the datasets, as
well as compute statistics from a queried/filtered dataset to be displayed on the
main dashboard of LyProX.

In the `views`, the `execute_query` function is called with the cleaned data from the
`DashboardForm`. This `execute_query` function then creates a combined query using
the fancy `Q` and `C` objects from `lydata`. These classes allow arbitrary combinations
of deferred queries to be created and only later be executed.

After executing the query, the filtered dataset is used to compute `Statistics` using
the `from_dataset` classmethod. This `pydantic.BaseModel` has similar fields to the
`DashboardForm` and is used to display the aggregated information of the filtered
dataset in the dashboard.
"""
import logging
import time
from collections.abc import Callable
from typing import Annotated, Any, Literal, TypeVar

import lydata  # noqa: F401
import lydata.utils as lyutils
import pandas as pd
from lydata import C
from lydata.accessor import QTypes
from pydantic import AfterValidator, BaseModel, computed_field, create_model

from lyprox.dataexplorer.loader import DataInterface  # noqa: F401
from lyprox.settings import LNLS

logger = logging.getLogger(__name__)


def assemble_selected_modalities(names: list[str]) -> dict[str, lyutils.ModalityConfig]:
    """Turn a list of modality names into a dictionary of modality configurations."""
    return {
        name: modality_config
        for name, modality_config in lyutils.get_default_modalities().items()
        if name in names
    }


def get_risk_factor_query(cleaned_form: dict[str, Any]) -> QTypes:
    """Create a query for the risk factors based on the cleaned form data."""
    risk_factor_query = C("dataset", "info", "name").isin(cleaned_form["datasets"])
    risk_factor_query &= C("t_stage").isin(cleaned_form["t_stage"])
    risk_factor_query &= C("subsite").isin(cleaned_form["subsite"])

    for short_names in ["smoke", "hpv", "surgery", "midext", "central"]:
        if cleaned_form[short_names] is not None:
            risk_factor_query &= C(short_names) == cleaned_form[short_names]

    if (is_n_plus := cleaned_form["is_n_plus"]) is not None:
        risk_factor_query &= C("n_stage") > 0 if is_n_plus else C("n_stage") == 0

    logger.debug(f"Query for risk factors: {risk_factor_query}")
    return risk_factor_query


def get_lnl_query(cleaned_form: dict[str, Any]) -> QTypes:
    """Create a query for the LNLs based on the cleaned form data."""
    lnl_query = None
    method = cleaned_form["modality_combine"]

    for side in ["ipsi", "contra"]:
        for lnl in LNLS:
            field = f"{side}_{lnl}"
            if cleaned_form[field] is not None:
                lnl_query &= C(method, side, lnl) == cleaned_form[field]

    logger.debug(f"Query for LNLs: {lnl_query}")
    return lnl_query


def execute_query(
    cleaned_form: dict[str, Any],
    dataset: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Execute a query on a dataset.

    After validating a `DashboardForm` by calling ``form.is_valid()``, the cleaned data
    is accessible as the attribute ``form.cleaned_data``. The returned dictionary should
    be passed to this function as the ``cleaned_form`` argument. Based on this cleaned
    form data, the involvement data from different modalities is combined using the
    `lydata` accessor method `lydata.LyDataAccessor.combine`. Then, a query is created
    using the `lydata.C` objects and executed on the dataset. The resulting filtered
    dataset is returned.

    If no dataset is provided, the default dataset is loaded from the `DataInterface`.
    """
    start_time = time.perf_counter()
    dataset = dataset or DataInterface().get_dataset()

    method = cleaned_form["modality_combine"]
    dataset[method] = dataset.ly.combine(
        modalities=assemble_selected_modalities(names=cleaned_form["modalities"]),
        method=method,
    )
    query = get_risk_factor_query(cleaned_form) & get_lnl_query(cleaned_form)
    queried_dataset = dataset.ly.query(query)
    end_time = time.perf_counter()

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
"""Keys may be ``True``, ``False``, or ``None``, while values are the counts of each."""
SexCounts = Annotated[
    dict[Literal["male", "female"], int],
    AfterValidator(make_ensure_keys_validator(keys=["male", "female"])),
]
"""Keys are ``male`` and ``female``, value are respective counts."""
TStageCounts = Annotated[
    dict[Literal[0, 1, 2, 3, 4], int],
    AfterValidator(make_ensure_keys_validator(keys=[0, 1, 2, 3, 4])),
]
"""Keys are the T-stages, values are the counts of each."""

T = TypeVar("T", bound="BaseStatistics")

class BaseStatistics(BaseModel):
    """
    Basic statistics to be computed and displayed on the dashboard.

    This defines the base class with counts of the basic patient and tumor information.
    It also defines the classmethod to compute the statistics from a dataset. In a
    dynamically created subclass of this one, the fields for every LNL ipsi- and
    contralaterally are added to the `Statistics` class.
    """
    datasets: dict[str, int]
    """How many patients are in each dataset."""
    sex: SexCounts
    """Number of male and female patients."""
    smoke: NullableBoolCounts
    """Number of patients who did or did not smoke."""
    hpv: NullableBoolCounts
    """Patients with or without HPV."""
    surgery: NullableBoolCounts
    """Number of patients that did or did not undergo surgery."""
    t_stage: TStageCounts
    """Counts of patients with different T-stages."""
    is_n_plus: NullableBoolCounts
    """Number of patients with or without N+ status."""
    subsite: dict[str, int]
    """Number of patients with tumors in different subsites."""
    central: NullableBoolCounts
    """For how many patients was the tumor located centrally, for how many not?"""
    midext: NullableBoolCounts
    """Number of patients with or without tumors crossing the midline."""

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
"""LNL fields, dynamically created for unpacking in the `pydantic.create_model` call."""

Statistics = create_model(
    "Statistics",
    __base__=BaseStatistics,
    **lnl_fields,
)
"""
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
"""

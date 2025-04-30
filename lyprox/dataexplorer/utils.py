"""Utility functions for data exploration and visualization."""

import logging
import time
from typing import Any

import pandas as pd
from lydata.utils import get_default_modalities
from pandas.io.formats.style import Styler

from lyprox.accounts.models import Institution
from lyprox.settings import LNLS

logger = logging.getLogger(__name__)


def smart_capitalize(value: str) -> str:
    """Only capitalize words that are not all caps (e.g. abbreviations)."""
    if all(c.isupper() for c in value):
        return value

    return value.capitalize()


def split_and_capitalize(value: str) -> str:
    """Split the string on underscores and capitalize each word.

    This is used to format the index of the `pandas.DataFrame` in the table view.
    """
    if value in LNLS:
        return value

    return " ".join([smart_capitalize(word) for word in value.split("_")])


def map_to_cell_classes(patients: pd.DataFrame) -> pd.DataFrame:
    """Return a class for each cell of the ``patients`` table."""
    consensus = "max_llh" if "max_llh" in patients.columns else "rank"
    classes_map = pd.DataFrame().reindex_like(patients).fillna("")
    modalities = [consensus, "sonography"] + list(get_default_modalities())

    for modality in modalities:
        if modality not in patients:
            continue
        for side in ["ipsi", "contra"]:
            classes_map[modality, side] = (
                pd.DataFrame()
                .reindex_like(patients[modality, side])
                .fillna("is-danger has-text-weight-bold has-text-white")
            )
            classes_map[modality, side] = classes_map[modality, side].where(
                cond=patients[modality, side] == True,  # noqa: E712
                other="is-success has-text-weight-bold has-text-white",
            )
            classes_map[modality, side] = classes_map[modality, side].where(
                cond=patients[modality, side].notna(),
                other="is-info has-text-weight-bold",
            )

    return pd.DataFrame(classes_map, columns=patients.columns, index=patients.index)


def bring_consensus_col_to_left(patients: pd.DataFrame) -> pd.DataFrame:
    """Make sure the consensus column is the third top-level column."""
    consensus = "max_llh" if "max_llh" in patients.columns else "rank"

    unordered_cols = patients.columns.get_level_values(0).unique().to_list()
    unordered_cols = [
        col for col in unordered_cols if col not in ["patient", "tumor", consensus]
    ]
    ordered_cols = ["patient", "tumor", consensus] + unordered_cols

    return patients[ordered_cols]


def get_institution_shortname(value: str) -> str:
    """Replace the institution names with their abbreviations."""
    return Institution.objects.get(name=value).shortname


def replace_nan(value: Any, replacement: str = "-") -> str:
    """Replace NaN values with ``replacement`` in the table view."""
    if pd.isna(value) or str(value).lower() in ["nan", "none"]:
        return replacement

    return value


def style_table(patients: pd.DataFrame) -> Styler:
    """Style the `pandas.DataFrame` HTML for better readability."""
    start_time = time.perf_counter()
    patients = bring_consensus_col_to_left(patients)
    cols_to_drop = [
        ("patient", "#", "id"),
        ("dataset", "info", "name"),
        ("total_dissected"),
        ("positive_dissected"),
        ("enbloc_dissected"),
        ("enbloc_positive"),
    ]
    result = (
        patients.drop(columns=cols_to_drop, errors="ignore")
        .style.format_index(
            formatter=split_and_capitalize,
            level=[0, 1, 2],
            axis=1,
        )
        .format(
            formatter=replace_nan,
        )
        .format(
            formatter=get_institution_shortname,
            subset=[("patient", "#", "institution")],
        )
        .set_sticky(axis="index")
        .set_sticky(axis="columns")
        .set_table_attributes("class='table'")
        .set_td_classes(map_to_cell_classes(patients))
        .set_properties(width="100%")
    )
    stop_time = time.perf_counter()
    logger.info(
        f"Styling the table took {stop_time - start_time:.2f} seconds. "
        f"Number of rows: {len(patients)}"
    )
    return result

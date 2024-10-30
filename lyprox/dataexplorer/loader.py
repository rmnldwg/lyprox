"""
The `DataInterface` class is used to load the patient cohort data into memory on server
start-up. It then provides a unified interface to access the data in different modules,
most importantly the `DataExplorer` module.
"""

import logging
from threading import Lock
from typing import Literal

import pandas as pd
from lydata import join_datasets

from lyprox.settings import GITHUB

logger = logging.getLogger(__name__)


class SingletonMeta(type):
    """Ensures that only one instance of the DataInterface class is created."""
    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        """Create a new instance of the class if it does not already exist."""
        with cls._lock:
            if cls not in cls._instances:
                logger.debug(f"Creating new instance of {cls}")
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
            else:
                logger.debug(f"Reusing existing instance of {cls}")

        return cls._instances[cls]


class DataInterface(metaclass=SingletonMeta):
    """Class to load the patient cohort data into memory on server start-up."""

    def __init__(self) -> None:
        """Initialize an empty public and private dataset."""
        self._data: dict[Literal["public", "private"], pd.DataFrame] = {}

    def load_and_enhance_data(
        self,
        year: int | str = "*",
        institution: str = "*",
        subsite: str = "*",
        repo: str = "rmnldwg/lydata",
        ref: str = "main",
    ) -> None:
        """
        Use `lydata` to load matching datasets from the specified repository.

        All arguments are directly passed to the `lydata.join_datasets` function. The
        method also infers sub- and superlevel involvement in case the data does not
        report either.

        The data is then stored according to the visibility of the repository. This
        ensures that during accessing, we can easily provide the correct data based on
        which user is requesting it.
        """
        visibility = GITHUB.get_repo(repo).visibility
        data = join_datasets(
            year=year,
            institution=institution,
            subsite=subsite,
            repo=repo,
            ref=ref,
        )
        data = data.join(data.ly.infer_sublevels())
        data = data.join(data.ly.infer_superlevels())

        logger.info(f"Loaded {len(data)} patients with visibility {visibility}")

        if visibility in self._data:
            data = pd.concat(
                [self._data[visibility], data],
                axis="index",
                ignore_index=True,
            )

        self._data[visibility] = data

    def delete_data(self, visibility: Literal["public", "private"]) -> None:
        """Delete the dataset with the specified visibility."""
        n = len(self._data[visibility])
        logger.info(f"Deleting all ({n}) {visibility} patients")
        del self._data[visibility]

    def get_data(self, visibility: Literal["public", "private"]) -> pd.DataFrame:
        """Return the dataset with the specified visibility."""
        logger.debug(f"Returning {visibility} data")
        return self._data[visibility].copy()

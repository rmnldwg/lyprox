"""
The `DataInterface` class is used to load the patient cohort data into memory on server
start-up. It then provides a unified interface to access the data in different modules,
most importantly the `DataExplorer` module.
"""

import logging
from threading import Lock
from typing import Literal

import pandas as pd
from lydata import available_datasets, join_datasets

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
    """
    Class to load the patient cohort data into memory on server start-up.

    All public methods are also thread-safe by using a lock. This may become important
    when the server is running in a multi-threaded environment and multiple threads
    try to access the data at the same time.
    """

    def __init__(self) -> None:
        """Initialize an empty public and private dataset."""
        self._data: dict[Literal["public", "private"], dict[str, pd.DataFrame]] = {}
        self._lock: Lock = Lock()

    def _load_and_enhance_data(
        self,
        year: int | str = "*",
        institution: str = "*",
        subsite: str = "*",
        repo: str = "rmnldwg/lydata",
        ref: str = "main",
    ) -> None:
        visibility = GITHUB.get_repo(repo).visibility

        if visibility not in self._data:
            self._data[visibility] = {}

        for dset_info in available_datasets(
            year=year,
            institution=institution,
            subsite=subsite,
            repo=repo,
            ref=ref,
        ):
            dset = dset_info.load(use_github=True)
            dset = dset.join(dset.ly.infer_sublevels())
            dset = dset.join(dset.ly.infer_superlevels())
            self._data[visibility][dset_info.name] = dset
            logger.info(
                f"Loaded {visibility} dataset {dset_info.name} ({len(dset)} patients)."
            )

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
        with self._lock:
            self._load_and_enhance_data(
                year=year,
                institution=institution,
                subsite=subsite,
                repo=repo,
                ref=ref,
            )

    def _delete_data(self, visibility: Literal["public", "private"]) -> None:
        logger.info(f"Deleting all {visibility} patients")
        del self._data[visibility]

    def delete_data(self, visibility: Literal["public", "private"]) -> None:
        """Delete the dataset with the specified visibility."""
        with self._lock:
            self._delete_data(visibility)

    def _get_datasets(self, visibility: Literal["public", "private"]) -> list[str]:
        return list(self._data[visibility].keys())

    def get_datasets(self, visibility: Literal["public", "private"]) -> list[str]:
        """Return the list of datasets with the specified visibility."""
        with self._lock:
            return self._get_datasets(visibility)

    def _get_data(
        self,
        visibility: Literal["public", "private"],
        datasets: list[str] | None = None,
    ) -> pd.DataFrame:
        datasets = datasets or self._get_datasets(visibility)
        logger.debug(f"Returning {visibility} datasets {datasets}")

        return pd.concat(
            [self._data[visibility][dset] for dset in datasets],
            axis="index",
            ignore_index=True,
        )

    def get_data(
        self,
        visibility: Literal["public", "private"],
        datasets: list[str] | None = None,
    ) -> pd.DataFrame:
        """Return the dataset with the specified visibility."""
        with self._lock:
            return self._get_data(visibility=visibility, datasets=datasets)

"""
The `DataInterface` class is used to load the patient cohort data into memory on server
start-up. It then provides a unified interface to access the data in different modules,
most importantly the `DataExplorer` module.
"""

import logging
from collections import namedtuple
from threading import Lock
from typing import Literal

import lydata
import lydata.utils as lyutils
import pandas as pd
from lydata.loader import LyDataset

logger = logging.getLogger(__name__)


DatasetStorage = namedtuple("DatasetStorage", ["visibility", "pushed_at", "dataframe"])


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


def load_with_metadata(dataset: LyDataset) -> pd.DataFrame:
    """Load a `LyDataset` and add columns with metadata to it."""
    repo = dataset.get_repo()
    dataframe = dataset.get_dataframe(use_github=True)
    dataframe = lyutils.infer_and_combine_levels(dataframe)

    dataframe["dataset", "info", "name"] = dataset.name
    dataframe["dataset", "info", "visibility"] = repo.visibility
    dataframe["dataset", "info", "pushed_at"] = repo.pushed_at

    return dataframe


class DataInterface(metaclass=SingletonMeta):
    """
    Class to load the patient cohort data into memory on server start-up.

    All public methods are also thread-safe by using a lock. This may become important
    when the server is running in a multi-threaded environment and multiple threads
    try to access the data at the same time.
    """

    def __init__(self) -> None:
        """Initialize an empty public and private dataset."""
        self._data: pd.DataFrame | None = None
        self._lock: Lock = Lock()

    def _add_dataset(self, dataset: pd.DataFrame) -> None:
        if self._data is None:
            self._data = dataset
        else:
            self._data = pd.concat(
                [self._data, dataset],
                axis="index",
                ignore_index=True,
            )

    def add_dataset(self, dataset: LyDataset) -> None:
        """Add a dataset to the data storage."""
        dataset = load_with_metadata(dataset)

        with self._lock:
            self._add_dataset(dataset=dataset)

        name = dataset["dataset", "info", "name"].iloc[0]
        logger.info(f"Added dataset {name} with {len(dataset)} patients")

    def _delete_dataset(self, name: str) -> int:
        has_name = self._data["dataset", "info", "name"] == name
        self._data = self._data.loc[~has_name]
        return has_name.sum()

    def delete_dataset(self, name: str) -> None:
        """Delete the dataset with the specified visibility."""
        with self._lock:
            num_deleted = self._delete_dataset(name=name)

        logger.info(f"Deleted dataset {name} with {num_deleted} patients")

    def get_dataset(self) -> pd.DataFrame:
        """Return the full dataset."""
        with self._lock:
            return self._data

    def load_and_enhance_datasets(
        self,
        year: int | str = "*",
        institution: str = "*",
        subsite: str = "*",
        repo_name: str = "rmnldwg/lydata",
        ref: str = "main",
        replace_existing: bool = False,
    ) -> None:
        """
        Use `lydata` to find and load matching datasets from the specified repository.

        All arguments are directly passed to the `lydata.join_datasets` function. The
        method also infers sub- and superlevel involvement in case the data does not
        report either.

        Some metadata, like the visibility, the dataset name, and the time the dataset
        was last pushed to the repository, are added to the concatenated dataframe in
        the storage of this interface singleton.
        """
        for dset in lydata.available_datasets(
            year=year,
            institution=institution,
            subsite=subsite,
            repo_name=repo_name,
            ref=ref,
            use_github=True,
        ):
            if (
                self._data is not None
                and dset.name in self._data["dataset", "info", "name"]
            ):
                if not replace_existing:
                    logger.info(f"Skip loading existing dataset {dset.name}")
                    continue

                logger.info(f"Replacing existing dataset {dset.name}")
                self.delete_dataset(dset.name)

            self.add_dataset(dset)

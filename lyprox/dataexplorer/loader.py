"""
The `DataInterface` class is used to load the patient cohort data into memory on server
start-up. It then provides a unified interface to access the data in different modules,
most importantly the `DataExplorer` module.
"""

import logging
from collections import namedtuple
from threading import Lock
from typing import Literal

import pandas as pd
from lydata import available_datasets
from lydata.utils import infer_all_levels

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


class DataInterface(metaclass=SingletonMeta):
    """
    Class to load the patient cohort data into memory on server start-up.

    All public methods are also thread-safe by using a lock. This may become important
    when the server is running in a multi-threaded environment and multiple threads
    try to access the data at the same time.
    """

    def __init__(self) -> None:
        """Initialize an empty public and private dataset."""
        self._data: dict[str, DatasetStorage] = {}
        self._lock: Lock = Lock()

    def _load_and_enhance_datasets(
        self,
        year: int | str = "*",
        institution: str = "*",
        subsite: str = "*",
        repo_name: str = "rmnldwg/lydata",
        ref: str = "main",
        replace_existing: bool = False,
    ) -> None:
        for dset_config in available_datasets(
            year=year,
            institution=institution,
            subsite=subsite,
            repo_name=repo_name,
            ref=ref,
            use_github=True,
        ):
            if dset_config.name in self._data:
                if not replace_existing:
                    logger.info(f"Skip loading existing dataset {dset_config.name}")
                    continue
                logger.info(f"Replacing existing dataset {dset_config.name}")
            else:
                logger.info(f"Loading new dataset {dset_config.name}")

            repo_name = dset_config.get_repo()
            dataframe = infer_all_levels(dset_config.get_dataframe(use_github=True))
            self._data[dset_config.name] = DatasetStorage(
                visibility=repo_name.visibility,
                pushed_at=repo_name.pushed_at,
                dataframe=dataframe,
            )

    def load_and_enhance_datasets(
        self,
        year: int | str = "*",
        institution: str = "*",
        subsite: str = "*",
        repo: str = "rmnldwg/lydata",
        ref: str = "main",
        replace_existing: bool = False,
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
            self._load_and_enhance_datasets(
                year=year,
                institution=institution,
                subsite=subsite,
                repo_name=repo,
                ref=ref,
                replace_existing=replace_existing,
            )

    def _get_datasets(self, visibility: Literal["public", "private"]) -> list[str]:
        return [d for d, s in self._data.items() if s.visibility == visibility]

    def get_datasets(self, visibility: Literal["public", "private"]) -> list[str]:
        """Return the list of dataset names with the specified visibility."""
        with self._lock:
            return self._get_datasets(visibility)

    def _delete_datasets(self, visibility: Literal["public", "private"]) -> None:
        logger.info(f"Deleting all {visibility} patients")
        for dset in self._get_datasets(visibility):
            del self._data[dset]

    def delete_datasets(self, visibility: Literal["public", "private"]) -> None:
        """Delete the dataset with the specified visibility."""
        with self._lock:
            self._delete_datasets(visibility)

    def _get_joined_data(
        self,
        visibility: Literal["public", "private"],
        datasets: list[str] | None = None,
    ) -> pd.DataFrame:
        datasets = datasets or self._get_datasets(visibility)
        logger.debug(f"Returning {visibility} datasets {datasets}")

        return pd.concat(
            [self._data[dset].dataframe for dset in datasets],
            axis="index",
            ignore_index=True,
        )

    def get_joined_data(
        self,
        visibility: Literal["public", "private"],
        datasets: list[str] | None = None,
    ) -> pd.DataFrame:
        """Return the dataset with the specified visibility."""
        with self._lock:
            return self._get_joined_data(visibility=visibility, datasets=datasets)

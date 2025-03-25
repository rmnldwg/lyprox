"""Defines a minimal model representing a dataset."""

import logging
import time

import pandas as pd
from django.db import models
from github import Repository
from joblib import Memory
from lydata.loader import LyDataset
from lydata.utils import infer_all_levels

from lyprox import loggers, settings
from lyprox.accounts.models import Institution

logger = logging.getLogger(__name__)
memory = Memory(location=settings.JOBLIB_CACHE_DIR, verbose=0)


@memory.cache
def cached_load_dataframe(
    year: int,
    institution: str,
    subsite: str,
    repo_name: str,
    ref: str,
) -> pd.DataFrame:
    """Load an enhanced dataset into a pandas DataFrame using a persistent cache."""
    lydataset = LyDataset(
        year=year,
        institution=institution,
        subsite=subsite,
        repo_name=repo_name,
        ref=ref,
    )
    df = lydataset.get_dataframe(use_github=True, token=settings.GITHUB_TOKEN)
    df = infer_all_levels(df)
    logger.info(f"Loaded dataset {lydataset} into DataFrame ({df.shape=}).")
    return df


class DatasetModel(loggers.ModelLoggerMixin, models.Model):
    """Minimal model representing a dataset.

    This is basically a Django representation of the
    :py:class:`~lydata.loader.LyDataset` class.

    Its :py:meth:`~DatasetModel.load_dataframe` method makes use of the function
    :py:func:`~cached_load_dataframe` to load the dataset into a pandas DataFrame.
    Note that this function uses `joblib`_ to cache the results of the function call
    in a persistent location given by the ``JOBLIB_CACHE_DIR`` setting.

    .. _joblib: https://joblib.readthedocs.io/en/stable/
    """

    year: int = models.IntegerField()
    institution: Institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    subsite: str = models.CharField(max_length=100)
    repo_name: str = models.CharField(max_length=100)
    ref: str = models.CharField(max_length=100)
    is_private: bool = models.BooleanField(default=False)
    last_pushed: models.DateTimeField = models.DateTimeField()
    last_saved: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options for the `DatasetModel`."""

        unique_together = ("year", "institution", "subsite")

    def save(self, *args, **kwargs) -> None:
        """Update the ``is_private`` field based on the GitHub repository."""
        repo = self.get_repo()
        self.is_private = repo.private
        self.last_pushed = repo.pushed_at
        return super().save(*args, **kwargs)

    @property
    def name(self) -> str:
        """Return the name of the dataset."""
        return f"{self.year}-{self.institution.shortname.lower()}-{self.subsite}"

    def __str__(self):
        """Return the name of the dataset."""
        return self.name

    def get_repo(self) -> Repository:
        """Return the GitHub repository object."""
        return settings.GITHUB.get_repo(self.repo_name)

    def get_kwargs(self) -> dict[str, int | str]:
        """Assemble ``kwargs`` from this model's field.

        These will both be used to call the :py:func:`~cached_load_dataframe` function
        as well as initialize a :py:class:`~lydata.loader.LyDataset` object.
        """
        return {
            "year": self.year,
            "institution": self.institution.shortname.lower(),
            "subsite": self.subsite,
            "repo_name": self.repo_name,
            "ref": self.ref,
        }

    def get_lydataset(self) -> LyDataset:
        """Create a :py:class:`~lydata.loader.LyDataset` from this model."""
        return LyDataset(**self.get_kwargs())

    def load_dataframe(self) -> pd.DataFrame:
        """Load the underlying table.

        This calls the :py:func:`~cached_load_dataframe` function with the assembled
        ``kwargs`` and returns the resulting DataFrame.
        """
        kwargs = self.get_kwargs()
        is_in_cache = cached_load_dataframe.check_call_in_cache(**kwargs)

        msg_add = "from cache." if is_in_cache else "from GitHub."

        start_time = time.perf_counter()
        table = cached_load_dataframe(**kwargs)
        elapsed_time = time.perf_counter() - start_time
        logger.info(f"Fetched dataset {self} in {elapsed_time:.2f}s {msg_add}")
        return table

"""Test the data loading singleton."""

from lydata.loader import LyDataset
from pytest import fixture

from lyprox.dataexplorer.loader import DataInterface


@fixture
def lydataset() -> LyDataset:
    """Return a LyDataset."""
    return LyDataset(
        year=2021,
        institution="usz",
        subsite="oropharynx",
        repo_name="rmnldwg/lydata",
        ref="main",
    )


def test_add_dataset(lydataset: LyDataset) -> None:
    """Test adding a dataset."""
    di = DataInterface()
    di.add_dataset(lydataset)
    assert set(di._data["dataset", "info", "name"].unique()) == {"2021-usz-oropharynx"}
    assert set(di._data["dataset", "info", "visibility"].unique()) == {"public"}
    assert len(di._data) == 287

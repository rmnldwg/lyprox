"""Test the data loading singleton."""

from lyprox.dataexplorer.loader import DataInterface


def test_added_dataset(data_interface: DataInterface) -> None:
    """Test adding a dataset."""
    assert (
        set(data_interface._data["dataset", "info", "name"].unique())
        == {
            "2021-usz-oropharynx",
            "2021-clb-oropharynx",
            "2023-isb-multisite",
            "2023-clb-multisite",
        }
    ), "Wrong datasets loaded"
    assert (
        set(data_interface._data["dataset", "info", "visibility"].unique())
        == {"public"}
    ), "Datasets have unexpected visibility"
    assert len(data_interface._data) == 1255, "Wrong number of patients loaded"

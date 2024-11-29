from pytest import fixture

from lyprox.dataexplorer.loader import DataInterface


@fixture(scope="session")
def data_interface() -> DataInterface:
    """Return a loaded data interface."""
    return DataInterface()

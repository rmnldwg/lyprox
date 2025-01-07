from collections import namedtuple
from typing import Any
from pytest import fixture

from lyprox.dataexplorer.forms import DashboardForm
from lyprox.dataexplorer.loader import DataInterface


@fixture(scope="session")
def data_interface() -> DataInterface:
    """Return a loaded data interface."""
    return DataInterface()


MockUser = namedtuple("MockUser", ["is_authenticated"])


@fixture
def cleaned_initial_form() -> dict[str, Any]:
    """Return the dashboard form's cleaned initial data."""
    initial_form = DashboardForm.from_initial(user=MockUser(is_authenticated=True))

    if not initial_form.is_valid():
        raise ValueError("Initial form is not valid.")

    return initial_form.cleaned_data

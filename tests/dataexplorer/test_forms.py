"""Test the forms of the dataexplorer app."""

from typing import Any

from pytest import fixture

from lyprox.dataexplorer.forms import DashboardForm


class MockUser:
    """Mock user class for testing."""
    def __init__(self, is_authenticated: bool) -> None:
        self.is_authenticated = is_authenticated


@fixture
def mock_user() -> MockUser:
    """Return a mock user."""
    return MockUser(is_authenticated=True)


@fixture
def initial_data(mock_user: MockUser) -> dict[str, Any]:
    """Return initial data for the form."""
    form = DashboardForm(user=mock_user)
    initial_data = {}
    for name, field in form.fields.items():
        initial_data[name] = form.get_initial_for_field(field, name)

    return initial_data


def test_initial_dashboard_form(initial_data: dict[str, Any], mock_user: MockUser) -> None:
    """Test the dashboard form with initial data."""
    form = DashboardForm(data=initial_data, user=mock_user)
    assert form.is_valid()

"""Test the forms of the dataexplorer app."""


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


def test_initial_dashboard_form(mock_user: MockUser) -> None:
    """Test the dashboard form with initial data."""
    form = DashboardForm.from_initial(user=mock_user)
    assert form.is_valid()

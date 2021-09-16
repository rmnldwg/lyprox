import pytest

from django import urls


@pytest.mark.parametrize(
    "url_name", [("patients:upload")]
)
def test_restricted_views(client, url_name):
    reversed_url = urls.reverse(url_name)
    response = client.get(reversed_url)
    assert response.status_code == 302
    assert urls.reverse("accounts:login") in response.url


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name", [("patients:list")]
)
def test_unrestricted_views(client, url_name):
    reversed_url = urls.reverse(url_name)
    response = client.get(reversed_url)
    assert response.status_code == 200

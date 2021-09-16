import pytest

from django import urls


@pytest.mark.parametrize(
    "url_name", 
    [("patients:upload"), 
     ("patients:download"), 
     ("patients:create"),] 
    #  ("patients:update"), 
    #  ("patients:delete"),
    #  ("patients:tumor_create"),
    #  ("patients:tumor_update"),
    #  ("patients:tumor_delete"), 
    #  ("patients:diagnose_create"), 
    #  ("patients:diagnose_update"), 
    #  ("patients:diagnose_delete")]
)
def test_restricted_views(client, url_name):
    reversed_url = urls.reverse(url_name)
    response = client.get(reversed_url)
    assert response.status_code == 302
    assert urls.reverse("accounts:login") in response.url


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name", 
    [("patients:list"), ]
    #  ("patients:detail")]
)
def test_unrestricted_views(client, url_name):
    reversed_url = urls.reverse(url_name)
    response = client.get(reversed_url)
    assert response.status_code == 200














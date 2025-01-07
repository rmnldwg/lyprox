"""
LyProX' URL configuration.

This defines the view for the landing page, the URLs for downloads and media and the
maintenance page. Otherwise it basically calls the URL configuration from the other
apps, `dataexplorer.urls` and `accounts.urls`.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("lyprox.accounts.urls")),
    path("dataexplorer/", include("lyprox.dataexplorer.urls")),
    path("riskpredictor/", include("lyprox.riskpredictor.urls")),
    path("", views.index, name="index"),
    path("maintenance/", views.maintenance, name="maintenance"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

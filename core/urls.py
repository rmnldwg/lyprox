"""
LyProX' URL configuration. This defines the view for the landing page, the URLs for
downloads and media and the maintenance page. Otherwise it basically calls the URL
configuration from the other apps, `patients.urls`, `dashboard.urls` and
`accounts.urls`.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path("patients/", include("patients.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("", views.index, name="index"),
    path("maintenance/", views.maintenance, name="maintenance"),
]

urlpatterns += static(
    settings.MEDIA_URL + "institution_logos/",
    document_root=settings.MEDIA_ROOT / "institution_logos",
)

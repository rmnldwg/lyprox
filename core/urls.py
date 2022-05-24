"""
LyProX' URL configuration.
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

urlpatterns += static(settings.DOWNLOADS_URL,
                      document_root=settings.DOWNLOADS_ROOT)
urlpatterns += static(settings.MEDIA_URL,
                      document_root=settings.MEDIA_ROOT)

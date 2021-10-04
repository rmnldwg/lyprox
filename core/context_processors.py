from django.conf import settings


def selected_settings(request):
    """Return dictionary of some selected settings."""
    return {
        "VERSION": settings.VERSION
    }
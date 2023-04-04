from django.apps import apps
from django.conf import settings


def selected_settings(request):
    """Return dictionary of some selected settings."""
    return {
        "VERSION": settings.VERSION,
        "IS_FROZEN": settings.IS_FROZEN,
        "FROZEN_VERSIONS": settings.FROZEN_VERSIONS,
    }

def navbar_apps(request):
    """Return dictionary of apps to add to the navbar."""
    context = {"navbar_apps": []}
    for app in apps.get_app_configs():
        if hasattr(app, "add_to_navbar") and app.add_to_navbar:
            name = app.name.split(".")[-1]
            context["navbar_apps"].append(name)

    return context

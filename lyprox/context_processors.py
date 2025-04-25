"""Context processors for the LyProX app.

These functions are called by Django when rendering templates. They add extra
information to the context available to the HTML templates. For example, `navbar_apps`
adds the name of all sub-apps in the LyProX web app to the context, such that the
navigation elements can be rendered everywhere.
"""

from typing import Any

from django.apps import apps
from django.conf import settings


def selected_settings(_request) -> dict[str, Any]:
    """Return dictionary of some selected settings."""
    return {
        "VERSION": settings.VERSION,
        "ADMIN_EMAIL": settings.ADMIN_EMAIL,
    }


def navbar_apps(_request) -> dict[str, Any]:
    """Return dictionary of apps to add to the navbar."""
    context = {"navbar_apps": []}
    for app in apps.get_app_configs():
        if hasattr(app, "add_to_navbar") and app.add_to_navbar:
            name = app.name.split(".")[-1]
            context["navbar_apps"].append(name)

    return context

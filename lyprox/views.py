"""
Define the home view and a maintenance view.
"""
from django.shortcuts import render


def index(request):
    """Return the landing page HTML.

    This adds the installed apps to the context where the ``add_to_navbar`` attribute
    is set to ``True``.
    """
    return render(request, "index.html", {})

def maintenance(request):
    """Redirect to maintenance page when `core.settings.MAINTENANCE` is ``True``."""
    return render(request, "maintenance.html", {})

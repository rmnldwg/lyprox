"""
Define the home view and a maintenance view.
"""
import logging
from typing import Any, Dict

import yaml
from django.shortcuts import render

from lyprox.settings import PUBLICATIONS_PATH

logger = logging.getLogger(__name__)


def add_publications_to_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """Add the publications stored in a YAML file to the context."""

    with open(PUBLICATIONS_PATH) as file:
        publications = yaml.safe_load(file)

    context["publications"] = publications["references"]
    return context


def index(request):
    """Return the landing page HTML.

    This adds the installed apps to the context where the ``add_to_navbar`` attribute
    is set to ``True``.

    It also adds the publications stored in a YAML file to the context.
    """
    context = add_publications_to_context(context={})
    return render(request, "index.html", context)

def maintenance(request):
    """Redirect to maintenance page when `core.settings.MAINTENANCE` is ``True``."""
    return render(request, "maintenance.html", {})

"""
Code that Django needs to register and load the app.

Beyond some bookkeeping, the `DataExplorerConfig` has a class attribute `add_to_navbar`
that is set to ``True`` and tells the `lyprox.context_processors.navbar_apps` context
processor to add an entry to the main navigation bar for this app.
"""

from django.apps import AppConfig


class DataExplorerConfig(AppConfig):
    """Configuration for the dataexplorer app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lyprox.dataexplorer'
    add_to_navbar = True
    """Tell the navbar context processor to add an entry for this app."""

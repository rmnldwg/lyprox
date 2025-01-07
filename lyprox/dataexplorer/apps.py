"""
Code that Django needs to register and load the app, as well as the patient records.

There are two custom things going on here:

1. The `DataExplorerConfig` has a class attribute `add_to_navbar` that is set to
   ``True`` and tells the `lyprox.context_processors.navbar_apps` context processor to
   add an entry to the main navigation bar for this app.
2. The `ready` method is called when the app is ready. It loads the datasets via the
   `DataInterface` class. The idea is to do this once at startup and then keep the patient
   records in memory for fast access.
"""

from django.apps import AppConfig

from lyprox.dataexplorer.loader import DataInterface


class DataExplorerConfig(AppConfig):
    """Configuration for the dataexplorer app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lyprox.dataexplorer'
    add_to_navbar = True
    """Tell the navbar context processor to add an entry for this app."""

    def ready(self):
        """Load the data into memory when the app is ready."""
        di = DataInterface()
        di.load_and_enhance_datasets(repo_name="rmnldwg/lydata")
        di.load_and_enhance_datasets(
            institution="hvh",
            repo_name="rmnldwg/lydata.private",
            ref="dib-update-paper",
        )
        di.load_and_enhance_datasets(
            institution="umcg",
            repo_name="rmnldwg/lydata.private",
            ref="2024-umcg-hypopharynx-larynx",
        )
        di.load_and_enhance_datasets(
            institution="usz",
            subsite="hypopharynx-larynx",
            repo_name="rmnldwg/lydata.private",
            ref="2023-usz-hypopharynx-larynx",
        )

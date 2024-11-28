from django.apps import AppConfig

from lyprox.dataexplorer.loader import DataInterface


class DataExplorerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lyprox.dataexplorer'
    add_to_navbar = True

    def ready(self):
        """Load the data into memory when the app is ready."""
        di = DataInterface()
        di.load_and_enhance_datasets(repo_name="rmnldwg/lydata")

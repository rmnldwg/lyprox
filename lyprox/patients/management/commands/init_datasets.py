"""Command to initialize patients."""

from django.core.management import base

from lyprox.accounts.models import User
from lyprox.patients.models import Dataset

INITIAL_DATASETS = [
    {
        "git_repo_url": "https://github.com/rmnldwg/lydata",
        "revision": "main",
        "data_path": "2021-usz-oropharynx/data.csv",
    },
    {
        "git_repo_url": "https://github.com/rmnldwg/lydata",
        "revision": "main",
        "data_path": "2021-clb-oropharynx/data.csv",
    },
    {
        "git_repo_url": "https://github.com/rmnldwg/lydata",
        "revision": "main",
        "data_path": "2023-isb-multisite/data.csv",
    },
    {
        "git_repo_url": "https://github.com/rmnldwg/lydata",
        "revision": "main",
        "data_path": "2023-clb-multisite/data.csv",
    },
    {
        "git_repo_url": "https://github.com/rmnldwg/lydata.private",
        "revision": "2023-usz-hypopharynx-larynx",
        "data_path": "2023-usz-hypopharynx-larynx/data.csv",
    },
    {
        "git_repo_url": "https://github.com/rmnldwg/lydata.private",
        "revision": "2023-hvh-oropharynx",
        "data_path": "2023-hvh-oropharynx/data.csv",
    },
]


class Command(base.BaseCommand):
    """Command to initialize patients."""
    help = __doc__

    def handle(self, *args, **options):
        """Execute command."""
        for kwargs in INITIAL_DATASETS:
            try:
                super_user = User.objects.get(is_superuser=True)
                dset = Dataset()
                dset.compute_fields(
                    **kwargs,
                    user_institution=super_user.institution,
                )
                dset.save()
                dset.import_csv_to_db()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Dataset '{kwargs['data_path']}' created."
                    )
                )
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"Dataset '{kwargs['data_path']}' could not be created: {exc}"
                    )
                )

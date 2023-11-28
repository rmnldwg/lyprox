"""
Management command to add patients from a file or via arguments.
"""
import json
from pathlib import Path
from django.core.management import base

from lyprox.accounts.models import User
from lyprox.patients.models import Dataset


class Command(base.BaseCommand):
    """Command to add patients from a file or via arguments."""
    help = __doc__

    def add_arguments(self, parser):
        """Add arguments to command."""
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--from-file",
            type=Path,
            help="Path to JSON file with list of patients.",
        )
        group.add_argument(
            "--from-stdin",
            action="store_true",
            help="Use command line arguments to create a single patient.",
        )
        parser.add_argument(
            "--git-repo-url", type=str, help="URL of git repository.",
        )
        parser.add_argument(
            "--revision", type=str, help="Revision of git repository.",
        )
        parser.add_argument(
            "--data-path", type=str, help="Path to patient CSV table in git repository.",
        )

    def handle(self, *args, **options):
        """Execute command."""
        if not options["from_stdin"]:
            with open(options["from_file"], "r", encoding="utf-8") as json_file:
                dataset_configurations = json.load(json_file)
        else:
            dataset_configurations = [{
                "git_repo_url": options["git_repo_url"],
                "revision": options["revision"],
                "data_path": options["data_path"],
            }]

        for config in dataset_configurations:
            try:
                super_user = User.objects.get(is_superuser=True)
                dset = Dataset()
                dset.compute_fields(
                    **config,
                    user_institution=super_user.institution,
                )
                dset.save()
                dset.import_csv_to_db()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Dataset '{config['data_path']}' created."
                    )
                )
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"Dataset '{config['data_path']}' could not be created: {exc}"
                    )
                )

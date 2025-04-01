"""Command to add datasets to database.

This convencience command allows adding individual dataset specifications manually or
several datasets at once from a JSON file. Note that this does not actually load the
data. The data is fetched and loaded into memory on demand, i.e., when a user opens
the data explorer.

This command works similar to the `add_institutions` and `add_users` commands. Here
is the help output of the command ``lyprox add_datasets --help``:

.. code-block:: text

    usage: lyprox add_datasets [-h] (--from-file FROM_FILE | --from-stdin)
                               [--year YEAR] [--institution INSTITUTION]
                               [--subsite SUBSITE] [--repo-name REPO_NAME]
                               [--ref REF] [--version] [-v {0,1,2,3}]
                               [--settings SETTINGS] [--pythonpath PYTHONPATH]
                               [--traceback] [--no-color] [--force-color]
                               [--skip-checks]

    Command to add datasets to database from initial JSON data.

    options:
      -h, --help            show this help message and exit
      --from-file FROM_FILE
                            Path to JSON file with list of risk models.
      --from-stdin          Use command line arguments to create a single risk
                            model.
      --year YEAR           Year of dataset.
      --institution INSTITUTION
                            Institution of dataset.
      --subsite SUBSITE     Subsite of dataset.
      --repo-name REPO_NAME
                            Name of repository.
      --ref REF             Reference of repository.
      --version             Show program's version number and exit.
      -v {0,1,2,3}, --verbosity {0,1,2,3}
                            Verbosity level; 0=minimal output, 1=normal output,
                            2=verbose output, 3=very verbose output
      --settings SETTINGS   The Python path to a settings module, e.g.
                            "myproject.settings.main". If this isn't provided, the
                            DJANGO_SETTINGS_MODULE environment variable will be
                            used.
      --pythonpath PYTHONPATH
                            A directory to add to the Python path, e.g.
                            "/home/djangoprojects/myproject".
      --traceback           Raise on CommandError exceptions.
      --no-color            Don't colorize the command output.
      --force-color         Force colorization of the command output.
      --skip-checks         Skip system checks.
"""

import json
from pathlib import Path

from django.core.management import base
from django.db import IntegrityError

from lyprox.accounts.models import Institution
from lyprox.dataexplorer.models import DatasetModel


class Command(base.BaseCommand):
    """Command to add datasets to database from initial JSON data."""

    help = __doc__

    def add_arguments(self, parser):
        """Add arguments to command."""
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--from-file",
            type=Path,
            help="Path to JSON file with list of risk models.",
        )
        group.add_argument(
            "--from-stdin",
            action="store_true",
            help="Use command line arguments to create a single risk model.",
        )
        parser.add_argument(
            "--year",
            type=int,
            help="Year of dataset.",
        )
        parser.add_argument(
            "--institution",
            type=str,
            help="Institution of dataset.",
        )
        parser.add_argument(
            "--subsite",
            type=str,
            help="Subsite of dataset.",
        )
        parser.add_argument(
            "--repo-name",
            type=str,
            help="Name of repository.",
        )
        parser.add_argument(
            "--ref",
            type=str,
            help="Reference of repository.",
        )

    def handle(self, *args, **options):
        """Execute command."""
        if not options["from_stdin"]:
            with open(options["from_file"], encoding="utf-8") as json_file:
                dataset_configs = json.load(json_file)
        else:
            dataset_configs = [
                {
                    "year": options["year"],
                    "institution": options["institution"],
                    "subsite": options["subsite"],
                    "repo_name": options["repo_name"],
                    "ref": options["ref"],
                }
            ]

        for config in dataset_configs:
            try:
                config["institution"] = Institution.objects.get(
                    shortname=config["institution"].upper(),
                )
                dataset = DatasetModel.objects.create(**config)
                table = dataset.load_dataframe()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully added dataset {dataset} with {table.shape=}."
                    )
                )
            except IntegrityError:
                self.stdout.write(
                    self.style.WARNING(
                        f"Dataset '{config['year']}-{config['institution']}-"
                        f"{config['subsite']}' already exists. Skipping."
                    )
                )
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(f"Failed to add dataset {config} due to {exc}.")
                )

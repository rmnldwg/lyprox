"""Command to add datasets to database."""

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
            "--year", type=int,
            help="Year of dataset.",
        )
        parser.add_argument(
            "--institution", type=str,
            help="Institution of dataset.",
        )
        parser.add_argument(
            "--subsite", type=str,
            help="Subsite of dataset.",
        )
        parser.add_argument(
            "--repo-name", type=str,
            help="Name of repository.",
        )
        parser.add_argument(
            "--ref", type=str,
            help="Reference of repository.",
        )

    def handle(self, *args, **options):
        """Execute command."""
        if not options["from_stdin"]:
            with open(options["from_file"], encoding="utf-8") as json_file:
                dataset_configs = json.load(json_file)
        else:
            dataset_configs = [{
                "year": options["year"],
                "institution": options["institution"],
                "subsite": options["subsite"],
                "repo_name": options["repo_name"],
                "ref": options["ref"],
            }]

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

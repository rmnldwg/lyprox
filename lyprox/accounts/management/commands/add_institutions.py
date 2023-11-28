"""
Management command to add institutions from a file or the command line.
"""
import json
from pathlib import Path
from django.core.management import base
from django.core.management.base import CommandParser
from django.db.utils import IntegrityError

from lyprox.accounts.models import Institution


class Command(base.BaseCommand):
    """Command to add institutions from a file or the command line."""
    help = __doc__

    def add_arguments(self, parser: CommandParser) -> None:
        """Add arguments to command."""
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--from-file",
            type=Path,
            help="Path to JSON file with list of institutions.",
        )
        group.add_argument(
            "--from-stdin",
            action="store_true",
            help="Use command line arguments to create a single institution.",
        )
        parser.add_argument(
            "--name", type=str, help="Name of institution.",
        )
        parser.add_argument(
            "--shortname", type=str, help="Abbreviation of institution.",
        )
        parser.add_argument(
            "--street", type=str, help="Street and house number of institution.",
        )
        parser.add_argument(
            "--city", type=str, help="City of institution.",
        )
        parser.add_argument(
            "--country", type=str, help="Country of institution.",
        )
        parser.add_argument(
            "--phone", type=str, help="Phone number of institution.",
        )
        parser.add_argument(
            "--logo", type=str, help="Path of insitution's logo within media.",
        )

    def handle(self, *args, **options):
        """Execute command."""
        if not options["from_stdin"]:
            with open(options["from_file"], "r", encoding="utf-8") as json_file:
                institution_configurations = json.load(json_file)
        else:
            institution_configurations = [{
                "name": options["name"],
                "shortname": options["shortname"],
                "street": options["street"],
                "city": options["city"],
                "country": options["country"],
                "phone": options["phone"],
                "logo": options["logo"],
            }]

        for config in institution_configurations:
            try:
                Institution.objects.create(**config)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Institution '{config['name']}' created."
                    )
                )
            except IntegrityError:
                self.stdout.write(
                    self.style.WARNING(
                        f"Institution '{config['name']}' already exists. Skipping."
                    )
                )
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"Could not create institution '{config['name']}': {exc}"
                    )
                )

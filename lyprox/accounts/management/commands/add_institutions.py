"""Management command to add institutions from a file or the command line.

With the command one may add institutions one at a time manually, by defining the
database fields of the `Institution` model, or by providing a JSON file with a list
of institutions to be added.

Default institutions are placed in the ``initial/institutions.json`` file. Adding
these initial institutions to the database is necessary whenever the database is
reset or the application is deployed for the first time.

After adding institutions, one can also `add_users` and `add_datasets`.

This is the output of the command ``lyprox add_institutions --help``:

.. code-block:: text

    usage: lyprox add_institutions [-h] (--from-file FROM_FILE | --from-stdin)
                                   [--name NAME] [--shortname SHORTNAME]
                                   [--street STREET] [--city CITY]
                                   [--country COUNTRY] [--phone PHONE]
                                   [--logo LOGO] [--version] [-v {0,1,2,3}]
                                   [--settings SETTINGS] [--pythonpath PYTHONPATH]
                                   [--traceback] [--no-color] [--force-color]
                                   [--skip-checks]

    Command to add institutions from a file or the command line.

    options:
      -h, --help            show this help message and exit
      --from-file FROM_FILE
                            Path to JSON file with list of institutions.
      --from-stdin          Use command line arguments to create a single
                            institution.
      --name NAME           Name of institution.
      --shortname SHORTNAME
                            Abbreviation of institution.
      --street STREET       Street and house number of institution.
      --city CITY           City of institution.
      --country COUNTRY     Country of institution.
      --phone PHONE         Phone number of institution.
      --logo LOGO           Path of insitution's logo within media.
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
            "--name",
            type=str,
            help="Name of institution.",
        )
        parser.add_argument(
            "--shortname",
            type=str,
            help="Abbreviation of institution.",
        )
        parser.add_argument(
            "--street",
            type=str,
            help="Street and house number of institution.",
        )
        parser.add_argument(
            "--city",
            type=str,
            help="City of institution.",
        )
        parser.add_argument(
            "--country",
            type=str,
            help="Country of institution.",
        )
        parser.add_argument(
            "--phone",
            type=str,
            help="Phone number of institution.",
        )
        parser.add_argument(
            "--logo",
            type=str,
            help="Path of insitution's logo within media.",
        )

    def handle(self, *args, **options):
        """Execute command."""
        if not options["from_stdin"]:
            with open(options["from_file"], encoding="utf-8") as json_file:
                institution_configurations = json.load(json_file)
        else:
            institution_configurations = [
                {
                    "name": options["name"],
                    "shortname": options["shortname"],
                    "street": options["street"],
                    "city": options["city"],
                    "country": options["country"],
                    "phone": options["phone"],
                    "logo": options["logo"],
                }
            ]

        for config in institution_configurations:
            try:
                Institution.objects.create(**config)
                self.stdout.write(
                    self.style.SUCCESS(f"Institution '{config['name']}' created.")
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

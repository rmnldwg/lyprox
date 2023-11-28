"""
Add users from a JSON file or via command line arguments.
"""
import json
import os
from pathlib import Path

from django.contrib.auth.hashers import make_password
from django.core.management import base
from django.db.utils import IntegrityError

from lyprox.accounts.models import Institution, User


class Command(base.BaseCommand):
    """Command to add users from a file or via arguments."""
    help = __doc__

    def add_arguments(self, parser):
        """Add arguments to command."""
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--from-file",
            type=Path,
            help="Path to JSON file with list of users.",
        )
        group.add_argument(
            "--from-stdin",
            action="store_true",
            help="Use command line arguments to create a single user.",
        )
        parser.add_argument(
            "--email", type=str, help="Email of user.",
        )
        parser.add_argument(
            "--first-name", type=str, help="First name of user.",
        )
        parser.add_argument(
            "--last-name", type=str, help="Last name of user.",
        )
        parser.add_argument(
            "--institution", type=str, help="Abbreviation of institution.",
        )
        parser.add_argument(
            "--is-active", action="store_true", default=True,
            help="Is user active?",
        )
        parser.add_argument(
            "--is-staff", action="store_true", default=False,
            help="Is user staff?",
        )
        parser.add_argument(
            "--is-superuser", action="store_true", default=False,
            help="Is user superuser?",
        )

    def handle(self, *args, **options):
        """Execute command."""
        if not options["from_stdin"]:
            with open(options["from_file"], "r", encoding="utf-8") as json_file:
                user_configurations = json.load(json_file)
        else:
            user_configurations = [{
                "email": options["email"],
                "first_name": options["first_name"],
                "last_name": options["last_name"],
                "institution": options["institution"],
                "is_active": options["is_active"],
                "is_staff": options["is_staff"],
                "is_superuser": options["is_superuser"],
            }]


        for config in user_configurations:
            env_name = (
                "DJANGO_"
                + config['email'].split('@')[0].upper().replace('.', '')
                + "_PASSWORD"
            )

            try:
                env_value = os.environ[env_name]
            except KeyError:
                self.stdout.write(
                    self.style.ERROR(
                        f"Environment variable '{env_name}' not found. Skipping."
                    )
                )
                continue

            try:
                config["password"] = make_password(env_value)
                config["institution"] = Institution.objects.get(shortname=config['institution'])
                User.objects.create(**config)
                self.stdout.write(
                    self.style.SUCCESS(f"User '{config['email']}' created.")
                )
            except IntegrityError:
                self.stdout.write(
                    self.style.WARNING(
                        f"User '{config['email']}' already exists. Skipping."
                    )
                )
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"User '{config['email']}' could not be created: {exc}"
                    )
                )

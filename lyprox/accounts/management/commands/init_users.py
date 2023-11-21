"""Command to initialize users."""
import os

from django.contrib.auth.hashers import make_password
from django.core.management import base
from django.db.utils import IntegrityError

from lyprox.accounts.models import Institution, User

INITIAL_USERS = [
    {
        "email": "roman.ludwig@usz.ch",
        "first_name": "Roman",
        "last_name": "Ludwig",
        "institution": "USZ",
        "is_active": True,
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "email": "jan.unkelbach@usz.ch",
        "first_name": "Jan",
        "last_name": "Unkelbach",
        "institution": "USZ",
        "is_active": True,
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "email": "vincent.gregoire@lyon.unicancer.fr",
        "first_name": "Vincent",
        "last_name": "Grégoire",
        "institution": "CLB",
        "is_active": True,
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "email": "roland.giger@insel.ch",
        "first_name": "Roland",
        "last_name": "Giger",
        "institution": "ISB",
        "is_active": True,
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "email": "lars.widmer@usz.ch",
        "first_name": "Lars",
        "last_name": "Widmer",
        "institution": "USZ",
        "is_active": True,
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "email": "esmee.looman@usz.ch",
        "first_name": "Esmee",
        "last_name": "Looman",
        "institution": "USZ",
        "is_active": True,
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "email": "yoel.perezhaas@usz.ch",
        "first_name": "Yoel",
        "last_name": "Perez Haas",
        "institution": "USZ",
        "is_active": True,
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "email": "julian.broennimann@uzh.ch",
        "first_name": "Julian",
        "last_name": "Brönnimann",
        "institution": "USZ",
        "is_active": True,
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "email": "sergi.benavente@vallhebron.cat",
        "first_name": "Sergio",
        "last_name": "Benavente Norza",
        "institution": "HVH",
        "is_active": True,
        "is_staff": False,
        "is_superuser": False,
    },
]


class Command(base.BaseCommand):
    """Command to initialize users."""
    help = __doc__

    def handle(self, *args, **options):
        """Execute command."""
        for user in INITIAL_USERS:
            env_name = (
                "DJANGO_"
                + user['email'].split('@')[0].upper().replace('.', '')
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
                user["password"] = make_password(env_value)
                user["institution"] = Institution.objects.get(shortname=user['institution'])
                User.objects.create(**user)
                self.stdout.write(
                    self.style.SUCCESS(f"User '{user['email']}' created.")
                )
            except IntegrityError:
                self.stdout.write(
                    self.style.WARNING(
                        f"User '{user['email']}' already exists. Skipping."
                    )
                )
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"User '{user['email']}' could not be created: {exc}"
                    )
                )

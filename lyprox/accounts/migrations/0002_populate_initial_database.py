"""
Create the initial institutions and users.
"""
import os

from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_initial_institutions(apps, schema_editor):
    """Create the institutions USZ, CLB, and ISB."""
    Institution = apps.get_model("accounts", "Institution")

    Institution.objects.create(
        name="University Hospital Zurich",
        shortname="USZ",
        street="Rämistrasse 100",
        city="Zürich",
        country="CH",
        phone="+41442553566",
        logo="logos/usz.png",
    )
    Institution.objects.create(
        name="Centre Léon Bérard",
        shortname="CLB",
        street="28 Rue Laennec",
        city="Lyon",
        country="FR",
        phone="+33478782828",
        logo="logos/clb.png",
    )
    Institution.objects.create(
        name="Inselspital Bern",
        shortname="ISB",
        street="Freiburgstrasse 15",
        city="Bern",
        country="CH",
        phone="+41316322111",
        logo="logos/isb.png",
    )


def create_initial_users(apps, schema_editor):
    """Create the initial users."""
    User = apps.get_model("accounts", "User")
    Institution = apps.get_model("accounts", "Institution")

    User.objects.create(
        email="roman.ludwig@usz.ch",
        first_name="Roman",
        last_name="Ludwig",
        institution=Institution.objects.get(shortname="USZ"),
        password=make_password(os.environ["DJANGO_ROMANLUDWIG_PASSWORD"]),
        is_active=True,
        is_staff=True,
        is_superuser=True,
    )
    User.objects.create(
        email="jan.unkelbach@usz.ch",
        first_name="Jan",
        last_name="Unkelbach",
        institution=Institution.objects.get(shortname="USZ"),
        password=make_password(os.environ["DJANGO_JANUNKELBACH_PASSWORD"]),
        is_active=True,
        is_staff=False,
        is_superuser=False,
    )
    User.objects.create(
        email="vincent.gregoire@lyon.unicancer.fr",
        first_name="Vincent",
        last_name="Grégoire",
        institution=Institution.objects.get(shortname="CLB"),
        password=make_password(os.environ["DJANGO_VINCENTGREGOIRE_PASSWORD"]),
        is_active=True,
        is_staff=False,
        is_superuser=False,
    )
    User.objects.create(
        email="roland.giger@insel.ch",
        first_name="Roland",
        last_name="Giger",
        institution=Institution.objects.get(shortname="ISB"),
        password=make_password(os.environ["DJANGO_ROLANDGIGER_PASSWORD"]),
        is_active=True,
        is_staff=False,
        is_superuser=False,
    )
    User.objects.create(
        email="lars.widmer@usz.ch",
        first_name="Lars",
        last_name="Widmer",
        institution=Institution.objects.get(shortname="USZ"),
        password=make_password(os.environ["DJANGO_LARSWIDMER_PASSWORD"]),
        is_active=True,
        is_staff=False,
        is_superuser=False,
    )
    User.objects.create(
        email="esmee.looman@usz.ch",
        first_name="Esmee",
        last_name="Looman",
        institution=Institution.objects.get(shortname="USZ"),
        password=make_password(os.environ["DJANGO_ESMEELOOMAN_PASSWORD"]),
        is_active=True,
        is_staff=False,
        is_superuser=False,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_initial_institutions),
        migrations.RunPython(create_initial_users),
    ]

"""Command to initialize institutions."""

from django.core.management import base
from django.db.utils import IntegrityError

from lyprox.accounts.models import Institution

INITIAL_INSTITUTIONS = [
    {
        "name": "University Hospital Zurich",
        "shortname": "USZ",
        "street": "Rämistrasse 100",
        "city": "Zürich",
        "country": "CH",
        "phone": "+41442553566",
        "logo": "logos/usz.png",
    },
    {
        "name": "Centre Léon Bérard",
        "shortname": "CLB",
        "street": "28 Rue Laennec",
        "city": "Lyon",
        "country": "FR",
        "phone": "+33478782828",
        "logo": "logos/clb.png",
    },
    {
        "name": "Inselspital Bern",
        "shortname": "ISB",
        "street": "Freiburgstrasse 15",
        "city": "Bern",
        "country": "CH",
        "phone": "+41316322111",
        "logo": "logos/isb.png",
    },
    {
        "name": "Vall d'Hebron Barcelona Hospital",
        "shortname": "HVH",
        "street": "Passeig de la Vall d'Hebron, 119-129",
        "city": "Barcelona",
        "country": "ES",
        "phone": "+34934893000",
        "logo": "logos/hvh.png",
    },
]


class Command(base.BaseCommand):
    """Command to initialize institutions."""
    help = __doc__

    def handle(self, *args, **options):
        """Execute command."""
        for institution in INITIAL_INSTITUTIONS:
            try:
                Institution.objects.create(**institution)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Institution '{institution['name']}' created."
                    )
                )
            except IntegrityError:
                self.stdout.write(
                    self.style.WARNING(
                        f"Institution '{institution['name']}' already exists. Skipping."
                    )
                )
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"Could not create institution '{institution['name']}': {exc}"
                    )
                )

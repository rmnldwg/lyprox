"""
This python script defines the ``makedownloadfiles`` command, which can be used
to generate CSV tables for each institution's cohort of patients that is in the
database.

.. code-block:: bash

    python manage.py makedownloadfiles

No other arguments needed.
"""
import io
import logging

from django.core.management.base import BaseCommand, CommandError

from patients.ioports import export_to_pandas
from accounts.models import Institution
from patients.models import Patient, CSVTable

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Export one CSV table per institution in the database and store them in
    a ``FileField`` of a model for later download.
    """
    help = __doc__

    def handle(self, *_args, **_options):
        """Execute the CSV table generation."""
        institutions = Institution.objects.all()
        for inst in institutions:
            buffer = io.StringIO()
            inst_queryset = Patient.objects.all().filter(institution=inst)

            try:
                inst_df = export_to_pandas(inst_queryset)
                logger.info(f"Exported {inst.shortname} patients to pandas")
            except Exception as exc:
                logger.error(exc)
                raise CommandError("Exporting failed.") from exc
            
            try:
                inst_df.to_csv(buffer, index=False)
                logger.info("Saved pandas to buffer")
            except Exception as exc:
                logger.error(exc)
                raise CommandError("Writing to buffer failed") from exc

            try:
                csv_table_qs = CSVTable.objects.filter(institution=inst)
                if not csv_table_qs.exists():
                    csv_table = CSVTable(
                        num_patients=len(inst_df),
                        institution=inst,
                    )
                else:
                    csv_table = csv_table_qs.first()
                csv_table.file.save("tmp.csv", buffer)
            except Exception as exc:
                logger.error(exc)
                raise CommandError(
                    "Creating new institution table object failed."
                ) from exc

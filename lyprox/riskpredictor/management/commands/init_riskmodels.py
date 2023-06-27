"""Command to initialize risk prediction models."""

from django.core.management import base

from lyprox.riskpredictor.models import InferenceResult

INITIAL_RISKMODELS = [
    {
        "git_repo_owner": "rmnldwg",
        "git_repo_name": "lynference",
        "revision": "win-graph-v1",
        "params_path": "params.yaml",
        "num_samples": 100,
    },
    {
        "git_repo_owner": "rmnldwg",
        "git_repo_name": "lynference",
        "revision": "complete-part1-v1",
        "params_path": "params.yaml",
        "num_samples": 100,
    },
    {
        "git_repo_owner": "rmnldwg",
        "git_repo_name": "lynference",
        "revision": "simple-IItoIII-v1",
        "params_path": "params.yaml",
        "num_samples": 100,
    },
]


class Command(base.BaseCommand):
    """Command to initialize risk prediction models."""
    help = __doc__

    def handle(self, *args, **options):
        """Execute command."""
        for kwargs in INITIAL_RISKMODELS:
            try:
                risk_model = InferenceResult(**kwargs)
                risk_model.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"InferenceResult '{kwargs['revision']}' created."
                    )
                )
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"InferenceResult '{kwargs['revision']}' could not be created: {exc}"
                    )
                )

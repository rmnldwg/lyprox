"""
Command to add risk prediction models to database.
"""
import json
from pathlib import Path
from django.core.management import base

from lyprox.riskpredictor.models import InferenceResult


class Command(base.BaseCommand):
    """Command to add risk prediction models to database."""
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
            "--git-repo-owner", type=str, default="rmnldwg",
            help="Owner of git repository.",
        )
        parser.add_argument(
            "--git-repo-name", type=str, default="lynference",
            help="Name of git repository.",
        )
        parser.add_argument(
            "--revision", type=str,
            help="Revision of git repository.",
        )
        parser.add_argument(
            "--params-path", type=str, default="params.yaml",
            help="Path to YAML params in git repository.",
        )
        parser.add_argument(
            "--num-samples", type=int, default=100,
            help="Number of samples used.",
        )

    def handle(self, *args, **options):
        """Execute command."""
        if not options["from_stdin"]:
            with open(options["from_file"], "r", encoding="utf-8") as json_file:
                riskmodel_configurations = json.load(json_file)
        else:
            riskmodel_configurations = [{
                "git_repo_owner": options["git_repo_owner"],
                "git_repo_name": options["git_repo_name"],
                "revision": options["revision"],
                "params_path": options["params_path"],
                "num_samples": options["num_samples"],
            }]

        for config in riskmodel_configurations:
            try:
                risk_model = InferenceResult(**config)
                risk_model.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"InferenceResult '{config['revision']}' created."
                    )
                )
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"InferenceResult '{config['revision']}' could not be created: {exc}"
                    )
                )

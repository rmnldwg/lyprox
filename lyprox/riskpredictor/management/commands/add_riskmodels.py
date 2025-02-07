"""Command to add risk prediction models to database."""

import json
from pathlib import Path

from django.core.management import base
from django.db import IntegrityError

from lyprox.riskpredictor.models import CheckpointModel


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
            "--repo-name",
            type=str,
            default="rmnldwg/lynference",
            help="Name of git repository.",
        )
        parser.add_argument(
            "--ref",
            type=str,
            default="main",
            help="Reference of git repository.",
        )
        parser.add_argument(
            "--graph-config-path",
            type=str,
            default="graph.ly.yaml",
            help="Path to YAML graph config in git repository.",
        )
        parser.add_argument(
            "--model-config-path",
            type=str,
            default="model.ly.yaml",
            help="Path to YAML model config in git repository.",
        )
        parser.add_argument(
            "--dist-configs-path",
            type=str,
            default="dists.ly.yaml",
            help="Path to YAML distribution configs in git repository.",
        )
        parser.add_argument(
            "--samples-path",
            type=str,
            default="models/samples.hdf5",
            help="Path to YAML params in git repository.",
        )
        parser.add_argument(
            "--num-samples",
            type=int,
            default=100,
            help="Number of samples used.",
        )

    def handle(self, *args, **options):
        """Execute command."""
        if not options["from_stdin"]:
            with open(options["from_file"], encoding="utf-8") as json_file:
                riskmodel_configs = json.load(json_file)
        else:
            riskmodel_configs = [
                {
                    "repo_name": options["repo_name"],
                    "ref": options["ref"],
                    "graph_config_path": options["graph_config_path"],
                    "model_config_path": options["model_config_path"],
                    "dist_configs_path": options["dist_configs_path"],
                    "samples_path": options["samples_path"],
                    "num_samples": options["num_samples"],
                }
            ]

        for config in riskmodel_configs:
            try:
                CheckpointModel.objects.create(**config)
                self.stdout.write(
                    self.style.SUCCESS(f"CheckpointModel '{config['ref']}' created.")
                )
            except IntegrityError:
                self.stdout.write(
                    self.style.WARNING(
                        f"CheckpointModel from repo_name='{config['repo_name']}' and "
                        f"ref='{config['ref']}' already exists."
                    )
                )
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"CheckpointModel from repo_name='{config['repo_name']}' and "
                        f"ref='{config['ref']}' could not be created doe to {exc}"
                    )
                )

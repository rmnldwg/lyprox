"""Command to add risk prediction models to database.

Adds definitions of risk models to the database. As with the `add_datasets` command,
this does not actually load and store the model samples in the database. Instead, those
are fetched and computed on demand using `joblib`_.

.. _joblib: https://joblib.readthedocs.io

The structure of the command is similar to the `add_institutions`, `add_users`, and
`add_datasets` commands. The command can be called with a JSON file containing a list
of risk model configurations or with command line arguments to create a single risk
model. The output of ``lyprox add_riskmodels --help`` is:

.. code-block:: text

    usage: lyprox add_riskmodels [-h] (--from-file FROM_FILE | --from-stdin)
                                 [--repo-name REPO_NAME] [--ref REF]
                                 [--graph-config-path GRAPH_CONFIG_PATH]
                                 [--model-config-path MODEL_CONFIG_PATH]
                                 [--dist-configs-path DIST_CONFIGS_PATH]
                                 [--samples-path SAMPLES_PATH]
                                 [--num-samples NUM_SAMPLES] [--version]
                                 [-v {0,1,2,3}] [--settings SETTINGS]
                                 [--pythonpath PYTHONPATH] [--traceback]
                                 [--no-color] [--force-color] [--skip-checks]

    Command to add risk prediction models to database.

    options:
      -h, --help            show this help message and exit
      --from-file FROM_FILE
                            Path to JSON file with list of risk models.
      --from-stdin          Use command line arguments to create a single risk
                            model.
      --repo-name REPO_NAME
                            Name of git repository.
      --ref REF             Reference of git repository.
      --graph-config-path GRAPH_CONFIG_PATH
                            Path to YAML graph config in git repository.
      --model-config-path MODEL_CONFIG_PATH
                            Path to YAML model config in git repository.
      --dist-configs-path DIST_CONFIGS_PATH
                            Path to YAML distribution configs in git repository.
      --samples-path SAMPLES_PATH
                            Path to YAML params in git repository.
      --num-samples NUM_SAMPLES
                            Number of samples used.
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

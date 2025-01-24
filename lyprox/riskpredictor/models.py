"""
Models for the `riskpredictor` Django app.

The model `InferenceResult` holds an upload of parameter samples that were produced
during an inference run of the ``lymph-model``. The samples should be fetched from the
DVC remote storage and used to compute the prior risk matrices.

Given a specific diagnosis, as entered via the `forms.DashboardForm`, the
``lymph-model`` package and the precomputed risk matrices in the `InferenceResult`
instances, the personalized risk estimates can be computed.
"""

import logging
import tempfile
from typing import Any

import emcee
import numpy as np
import yaml
from django.db import models
from dvc.api import DVCFileSystem
from github import Github, Repository
from joblib import Memory
from lydata.loader import _get_github_auth
from lymph.types import Model
from lyscripts.configs import (
    DeprecatedModelConfig,
    DistributionConfig,
    GraphConfig,
    ModelConfig,
    add_dists,
    construct_model,
)
from pydantic import TypeAdapter

from lyprox import loggers, settings

logger = logging.getLogger(__name__)
memory = Memory(location=settings.JOBLIB_CACHE_DIR, verbose=0)


def fetch_and_merge_yaml(
    repo_name: str,
    ref: str,
    graph_config_path: str,
    model_config_path: str,
    distributions_config_path: str,
) -> dict[str, Any]:
    """Fetch and merge the YAML configuration files from the repo."""
    repo_url = f"https://github.com/{repo_name}"
    dvc_fs = DVCFileSystem(url=repo_url, rev=ref)
    config_paths = [graph_config_path, model_config_path, distributions_config_path]
    merged_config = {}
    for config_path in config_paths:
        with dvc_fs.open(config_path) as config_file:
            config_dict = yaml.safe_load(config_file)
            merged_config.update(config_dict)

    return merged_config


def validate_configs(
    merged_yaml: dict[str, Any],
) -> tuple[GraphConfig, ModelConfig, dict[str | int, DistributionConfig]]:
    """Validate the pydantic configs necessary for constructing the model."""
    graph_config = GraphConfig.model_validate(merged_yaml["graph"])

    if merged_yaml.get("version") != 1:
        deprecated = DeprecatedModelConfig.model_validate(merged_yaml["model"])
        model_config, distributions_config = deprecated.translate()
        return graph_config, model_config, distributions_config

    model_config = ModelConfig.model_validate(merged_yaml["model"])
    adapter = TypeAdapter(dict[str | int, DistributionConfig])
    distributions_config = adapter.validate_python(merged_yaml["distributions"])
    return graph_config, model_config, distributions_config


def construct_model_and_add_dists(
    graph_config: GraphConfig,
    model_config: ModelConfig,
    distributions_config: dict[str | int, DistributionConfig],
) -> Model:
    """Construct the lymph model and add the distributions to it."""
    model = construct_model(model_config=model_config, graph_config=graph_config)
    return add_dists(model=model, distributions=distributions_config)


def fetch_model_samples(
    repo_name: str,
    ref: str,
    samples_path: str,
    num_samples: int,
    seed: int = 42,
) -> np.ndarray:
    """Fetch the model samples from the HDF5 file in the DVC repo."""
    repo_url = f"https://github.com/{repo_name}"
    dvc_fs = DVCFileSystem(url=repo_url, rev=ref)

    with tempfile.NamedTemporaryFile() as temp_file:
        dvc_fs.get_file(samples_path, temp_file.name)
        hdf5_backend = emcee.backends.HDFBackend(
            filename=temp_file.name,
            read_only=True,
        )
        samples = hdf5_backend.get_chain(flat=True)

    rng = np.random.default_rng(seed)
    rand_idx = rng.choice(
        a=len(samples),
        size=num_samples,
        replace=False,
    )
    return samples[rand_idx]


def compute_priors(
    model: Model,
    samples: np.ndarray,
    t_stage: str | int,
) -> np.ndarray:
    """Compute the prior state dists for the given model, samples, and t_stage."""
    priors = []

    for sample in samples:
        model.set_params(*sample)
        priors.append(model.state_dist(t_stage=t_stage))

    return np.stack(priors)


class InferenceResult(loggers.ModelLoggerMixin, models.Model):
    """
    Results of an inference run of the ``lymph-model`` package.

    It fetches the HDF5 parameter samples from the DVC remote storage and uses them to
    compute the prior risk matrices and stores them in an HDF5 file, too.
    """

    repo_name = models.CharField(max_length=50, default="rmnldwg/lynference")
    """Identifier of the GitHub repository that contains the trained model."""
    ref = models.CharField(max_length=40, default="main")
    """Git reference of the trained model. E.g., a commit hash, tag, or branch name."""
    graph_config_path = models.CharField(max_length=100, default="graph.ly.yaml")
    """Path to YAML file containing the graph configuration inside the git repo."""
    model_config_path = models.CharField(max_length=100, default="model.ly.yaml")
    """Path to YAML file containing the model configuration inside the git repo."""
    distributions_config_path = models.CharField(
        max_length=100,
        default="distributions.ly.yaml",
    )
    """Path to YAML file defining the distributions over diagnose times."""
    samples_path = models.CharField(max_length=100, default="models/samples.hdf5")
    """Path to HDF5 file containing the parameter samples inside the git repo."""
    num_samples = models.PositiveIntegerField(default=100)
    """Number of samples to use for computing the prior risk matrices."""

    class Meta:
        """Meta options for the `InferenceResult` model."""

        unique_together = ("repo_name", "ref")

    def get_repo(
        self,
        token: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> Repository:
        """Return the GitHub repository object."""
        auth = _get_github_auth(token=token, user=user, password=password)
        gh = Github(auth=auth)
        repo = gh.get_repo(self.repo_name)
        logger.info(f"Fetched GitHub repository {self.repo_name}")
        return repo

    def get_merged_yaml(self) -> dict[str, Any]:
        """Fetch and merge the YAML configuration files from the repo."""
        return memory.cache(fetch_and_merge_yaml)(
            repo_name=self.repo_name,
            ref=self.ref,
            graph_config_path=self.graph_config_path,
            model_config_path=self.model_config_path,
            distributions_config_path=self.distributions_config_path,
        )

    def validate_configs(
        self,
    ) -> tuple[GraphConfig, ModelConfig, dict[str | int, DistributionConfig]]:
        """Validate the pydantic configs necessary for constructing the model."""
        merged_yaml = self.get_merged_yaml()
        return validate_configs(merged_yaml)

    def create_model(self) -> Model:
        """Create the lymph model instance from the validated configs."""
        graph_config, model_config, distributions_config = self.validate_configs()
        return memory.cache(construct_model_and_add_dists)(
            graph_config=graph_config,
            model_config=model_config,
            distributions_config=distributions_config,
        )

    def fetch_samples(self) -> np.ndarray:
        """Fetch the model samples from the HDF5 file in the DVC repo."""
        return memory.cache(fetch_model_samples)(
            repo_name=self.repo_name,
            ref=self.ref,
            samples_path=self.samples_path,
            num_samples=self.num_samples,
        )

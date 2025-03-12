"""Models for the `riskpredictor` Django app.

The model `CheckpointModel` holds an upload of parameter samples that were produced
during an inference run of the ``lymph-model``. The samples should be fetched from the
DVC remote storage and used to compute the prior risk matrices.

Given a specific diagnosis, as entered via the `forms.RiskpredictorForm`, the
``lymph-model`` package and the precomputed risk matrices in the `CheckpointModel`
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
from joblib import Memory
from lymph.models import HPVUnilateral, Midline, Unilateral
from lymph.types import Model
from lyscripts.configs import (
    DeprecatedModelConfig,
    DistributionConfig,
    GraphConfig,
    ModelConfig,
    add_distributions,
    construct_model,
)
from pydantic import TypeAdapter

from lyprox import loggers, settings

logger = logging.getLogger(__name__)
memory = Memory(location=settings.JOBLIB_CACHE_DIR, verbose=0)


@memory.cache
def cached_fetch_and_merge_yaml(
    repo_name: str,
    ref: str,
    graph_config_path: str,
    model_config_path: str,
    dist_configs_path: str,
) -> dict[str, Any]:
    """Fetch and merge the YAML configuration files from the repo."""
    repo_url = f"https://github.com/{repo_name}"
    dvc_fs = DVCFileSystem(url=repo_url, rev=ref)
    config_paths = [graph_config_path, model_config_path, dist_configs_path]
    merged_config = {}
    for config_path in config_paths:
        with dvc_fs.open(config_path) as config_file:
            config_dict = yaml.safe_load(config_file)
            merged_config.update(config_dict)

    return merged_config


ConfigAndVersionTupleType = tuple[
    GraphConfig, ModelConfig, dict[str | int, DistributionConfig], int
]


def validate_configs(merged_yaml: dict[str, Any]) -> ConfigAndVersionTupleType:
    """Validate the pydantic configs necessary for constructing the model."""
    graph_config = GraphConfig.model_validate(merged_yaml["graph"])
    version = merged_yaml.get("version", 0)

    if version != 1:
        deprecated = DeprecatedModelConfig.model_validate(merged_yaml["model"])
        model_config, dist_configs = deprecated.translate()
        return graph_config, model_config, dist_configs, version

    model_config = ModelConfig.model_validate(merged_yaml["model"])
    adapter = TypeAdapter(dict[str | int, DistributionConfig])
    dist_configs = adapter.validate_python(merged_yaml["distributions"])
    return graph_config, model_config, dist_configs, version


@memory.cache
def cached_construct_model_and_add_dists(
    graph_config: GraphConfig,
    model_config: ModelConfig,
    dist_configs: dict[str | int, DistributionConfig],
    version: int,
) -> Model:
    """Construct the lymph model and add the distributions to it."""
    model = construct_model(model_config=model_config, graph_config=graph_config)
    model = add_distributions(model=model, configs=dist_configs)

    if version == 0 and isinstance(model, Midline):
        # This is necessary, since the previous version of the midline model did not
        # have the `midext_prob` parameter. We set it to 0.5 and ignore it for setting
        # the parameters to recreate the old behavior (at least as long as `midext` is
        # always provided).
        model.set_params(midext_prob=0.5)
        logger.debug("Set `midext_prob=0.5` for the deprecated Midline model.")
        params = list(model.get_params())
        params.remove("midext_prob")
        model.named_params = params
        logger.debug(f"Set named params to {params} for the deprecated Midline model.")

    return model


@memory.cache
def cached_fetch_model_samples(
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


@memory.cache
def cached_compute_priors(
    model: Model,
    samples: np.ndarray,
    t_stage: str | int,
) -> np.ndarray:
    """Compute the prior state dists for the given model, samples, and t_stage."""
    priors = []

    for sample in samples:
        model.set_named_params(*sample)
        priors.append(model.state_dist(t_stage=t_stage))

    return np.stack(priors)


class CheckpointModel(loggers.ModelLoggerMixin, models.Model):
    """Results of an inference run of the ``lymph-model`` package.

    It fetches the HDF5 parameter samples from the DVC remote storage and uses them to
    compute the prior risk matrices and caches them using joblib.
    """

    repo_name = models.CharField(max_length=50, default="rmnldwg/lynference")
    """Identifier of the GitHub repository that contains the trained model."""
    ref = models.CharField(max_length=40, default="main")
    """Git reference of the trained model. E.g., a commit hash, tag, or branch name."""
    graph_config_path = models.CharField(max_length=100, default="graph.ly.yaml")
    """Path to YAML file containing the graph configuration inside the git repo."""
    model_config_path = models.CharField(max_length=100, default="model.ly.yaml")
    """Path to YAML file containing the model configuration inside the git repo."""
    dist_configs_path = models.CharField(
        max_length=100,
        default="distributions.ly.yaml",
    )
    """Path to YAML file defining the distributions over diagnose times."""
    samples_path = models.CharField(max_length=100, default="models/samples.hdf5")
    """Path to HDF5 file containing the parameter samples inside the git repo."""
    num_samples = models.PositiveIntegerField(default=100)
    """Number of samples to use for computing the prior risk matrices."""

    class Meta:
        """Meta options for the `CheckpointModel`."""

        unique_together = (
            "repo_name",
            "ref",
            "graph_config_path",
            "model_config_path",
            "dist_configs_path",
            "samples_path",
        )

    def __str__(self) -> str:
        """Return the string representation of the instance."""
        return f"{self.repo_name}@{self.ref}"

    def get_merged_yaml(self) -> dict[str, Any]:
        """Fetch and merge the YAML configuration files from the repo."""
        return cached_fetch_and_merge_yaml(
            repo_name=self.repo_name,
            ref=self.ref,
            graph_config_path=self.graph_config_path,
            model_config_path=self.model_config_path,
            dist_configs_path=self.dist_configs_path,
        )

    def validate_configs(self) -> ConfigAndVersionTupleType:
        """Validate the pydantic configs necessary for constructing the model."""
        merged_yaml = self.get_merged_yaml()
        return validate_configs(merged_yaml)

    def construct_model(self) -> Model:
        """Create the lymph model instance from the validated configs."""
        graph_config, model_config, dist_configs, version = self.validate_configs()
        return cached_construct_model_and_add_dists(
            graph_config=graph_config,
            model_config=model_config,
            dist_configs=dist_configs,
            version=version,
        )

    @property
    def is_unilateral(self) -> bool:
        """Check if the model is a `Unilateral` model."""
        return isinstance(self.construct_model(), Unilateral | HPVUnilateral)

    @property
    def is_midline(self) -> bool:
        """Check if the model is a `Midline` model."""
        return isinstance(self.construct_model(), Midline)

    def fetch_samples(self) -> np.ndarray:
        """Fetch the model samples from the HDF5 file in the DVC repo."""
        return cached_fetch_model_samples(
            repo_name=self.repo_name,
            ref=self.ref,
            samples_path=self.samples_path,
            num_samples=self.num_samples,
        )

    def compute_priors(self, t_stage: int | str) -> np.ndarray:
        """Compute priors for every T-stage using the model samples."""
        return cached_compute_priors(
            model=self.construct_model(),
            samples=self.fetch_samples(),
            t_stage=t_stage,
        )

    def precompute_priors(self) -> None:
        """Precompute the priors for all T-stages and cache them."""
        for t_stage in self.construct_model().get_all_distributions():
            priors = self.compute_priors(t_stage=t_stage)
            self.logger.info(
                f"{self} precomputed prior for {t_stage=} with {priors.shape=}."
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Fill the cache with precomputed priors before saving the instance."""
        self.precompute_priors()
        return super().save(*args, **kwargs)

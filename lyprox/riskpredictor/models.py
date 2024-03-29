"""
The model `InferenceResult` holds an upload of parameter samples that were produced
during an inference run of the ``lymph-model``. The samples should be fetched from the
DVC remote storage and used to compute the prior risk matrices.

Given a specific diagnosis, as entered via the `forms.RiskForm`, the ``lymph-model``
package and the precomputed risk matrices in the `InferenceResult` instances, the
personalized risk estimates can be computed.
"""
import io
from pathlib import Path
from typing import Any, Dict, Optional, Union

import h5py
import lyscripts
import numpy as np
import yaml
from django.db import models
from dvc.api import DVCFileSystem
from github import Github, GithubException
from lymph import Bilateral, MidlineBilateral, Unilateral

from lyprox import settings

from .. import loggers


def get_path_for_risk_matrices(instance, filename):
    """
    Returns the path where the risk matrices should be stored for a given
    `InferenceResult` instance.
    """
    repo_path = instance.git_repo_url.split("//")[-1]
    return f"risk/{repo_path}/{instance.revision}.hdf5"


class InferenceResult(loggers.ModelLoggerMixin, models.Model):
    """Results of an inference run of the ``lymph-model`` package.

    It fetches the HDF5 parameter samples from the DVC remote storage and uses them to
    compute the prior risk matrices and stores them in an HDF5 file, too.
    """
    git_repo_owner = models.CharField(max_length=50, default="rmnldwg")
    """Owner of the GitHub repository that contains the trained model."""
    git_repo_name = models.CharField(max_length=50, default="lynference")
    """Name of the GitHub repository that contains the trained model."""
    revision = models.CharField(max_length=40, default="main")
    """Git revision of the trained model. E.g., a commit hash, tag, or branch name."""
    params_path = models.CharField(max_length=100, default="params.yaml")
    """Path to the YAML file containing the model parameters inside the git repo."""
    params = models.JSONField(default=dict)
    """Parameters to recreate lymph model for risk prediction."""
    description = models.TextField(default="")
    """GitHub release description of the inference run."""
    risk_matrices = models.FileField(upload_to=get_path_for_risk_matrices)
    """HDF5 file containing the computed prior risk matrices."""
    num_samples = models.PositiveIntegerField(default=100)
    """Number of samples to use for computing the prior risk matrices."""


    class Meta:
        unique_together = ("git_repo_owner", "git_repo_name", "revision")


    def __str__(self):
        return f"{self.git_repo_url}/tree/{self.revision}"

    @property
    def git_repo_url(self):
        """Return the URL of the GitHub repository."""
        return f"https://github.com/{self.git_repo_owner}/{self.git_repo_name}"

    @property
    def lnls(self):
        """Return list of lymph node levels."""
        return list(self.params["graph"]["lnl"].keys())

    @property
    def t_stages(self):
        """Return list of tumor stages."""
        return self.params["model"]["t_stages"]

    @property
    def is_bilateral(self):
        """Return whether the model is bilateral."""
        lymph_model = self.get_lymph_model()
        return isinstance(lymph_model, (Bilateral, MidlineBilateral))

    @property
    def is_midline(self):
        """Return whether the model is midline."""
        lymph_model = self.get_lymph_model()
        return isinstance(lymph_model, MidlineBilateral)

    @property
    def lnls(self):
        """Return a list with the names of the included LNLs."""
        return list(self.params["graph"]["lnl"].keys())


    @staticmethod
    def fetch_params(
        dvc_file_system: DVCFileSystem,
        params_path: Union[Path, str],
    ) -> Dict[str, Any]:
        """Load the model parameters from the YAML file in the DVC repo."""
        with dvc_file_system.open(params_path) as params_file:
            params = yaml.safe_load(params_file)
        return params


    @staticmethod
    def fetch_samples(
        dvc_file_system: DVCFileSystem,
        samples_path: str,
        num_samples: int = 100,
    ) -> np.ndarray:
        """Load the model samples from the HDF5 file in the DVC repo."""
        with dvc_file_system.open(samples_path) as samples_file:
            with h5py.File(samples_file, "r") as samples_h5:
                raw_chain = samples_h5["mcmc/chain"][:]
                num_dims = raw_chain.shape[-1]
                samples = raw_chain.reshape((-1, num_dims))
                rand_idx = np.random.choice(
                    samples.shape[0], size=num_samples, replace=False
                )
                samples = samples[rand_idx]

        return samples


    def fetch_description(self) -> str:
        """Fetch the release description from the GitHub API."""
        try:
            gh = Github(login_or_token=settings.GITHUB_TOKEN)
            repo = gh.get_repo(f"{self.git_repo_owner}/{self.git_repo_name}")
            release = repo.get_release(id=self.revision)
            return release.body

        except GithubException:
            return "This revision has no release description."


    def compute_risk_matrices(self, lymph_model, t_stages, samples) -> np.ndarray:
        """Compute the risk matrices for the given model and samples."""
        per_sample_risk_shape = lymph_model.risk(
            given_params=samples.mean(axis=0),
            t_stage=t_stages[0],
        ).shape

        risk_shape = (self.num_samples, *per_sample_risk_shape)

        if self.is_midline:
            risk_matrices = {}
            for stage in t_stages:
                risk_matrices[f"{stage}/ext"] = np.empty(shape=risk_shape)
                risk_matrices[f"{stage}/noext"] = np.empty(shape=risk_shape)
        else:
            risk_matrices = {stage: np.empty(shape=risk_shape) for stage in t_stages}

        for i, sample in enumerate(samples):
            lymph_model.check_and_assign(sample)
            for stage in t_stages:
                if self.is_midline:
                    risk_matrices[f"{stage}/ext"][i] = lymph_model.risk(
                        t_stage=stage, midline_extension=True
                    )
                    risk_matrices[f"{stage}/noext"][i] = lymph_model.risk(
                        t_stage=stage, midline_extension=False
                    )
                else:
                    risk_matrices[stage][i] = lymph_model.risk(t_stage=stage)

        self.logger.info("Computed risk matrices for T-categories %s", t_stages)
        return risk_matrices


    def store_risk_matrices(self, risk_matrices):
        """Store the risk matrices in the HDF5 file field on disk."""
        bytes_io = io.BytesIO()
        with h5py.File(bytes_io, "w") as h5_file:
            for h5_path, risk_matrix in risk_matrices.items():
                h5_file.create_dataset(h5_path, data=risk_matrix)

        self.risk_matrices.save(
            get_path_for_risk_matrices(self, "_"), bytes_io, save=False
        )

        self.logger.info("Stored risk matrices in %s", self.risk_matrices.path)


    def load_risk_matrices(
        self,
        t_stage: str,
        midline_extension: Optional[bool] = None,
    ) -> np.ndarray:
        """Load the precomputed and stored prior risk matrices for the given tumor
        stage and lateralization.
        """
        if self.is_midline and midline_extension is None:
            raise ValueError(
                "For MidlineBilateral models, the lateralization must be specified."
            )

        with h5py.File(self.risk_matrices.path, "r") as h5_file:
            if self.is_midline:
                key = f"{t_stage}/{'ext' if midline_extension else 'noext'}"
            else:
                key = t_stage

            return h5_file[key][:]


    def get_lymph_model(self) -> Union[Unilateral, Bilateral, MidlineBilateral]:
        """Get (create if necessary) lymph model instance from the stored params."""
        if hasattr(self, "_lymph_model"):
            return self._lymph_model

        self._lymph_model = lyscripts.utils.create_model_from_config(self.params)
        return self._lymph_model


    def save(self, *args, **kwargs) -> None:
        """Compute the risk matrices and store them in the HDF5 file."""
        self.description = self.fetch_description()

        dvc_file_system = DVCFileSystem(url=self.git_repo_url, rev=self.revision)
        self.params = self.fetch_params(dvc_file_system, self.params_path)

        t_stages = self.params.get("models", {}).get("t_stages", ["early", "late"])
        samples_path = self.params.get("general", {}).get("samples", "models/samples.hdf5")
        samples = self.fetch_samples(dvc_file_system, samples_path, self.num_samples)
        self.logger.info("Loaded samples with dimensions %s", samples.shape)

        lymph_model = self.get_lymph_model()
        self.logger.info("Created trained lymph model %s", lymph_model)

        risk_matrices = self.compute_risk_matrices(lymph_model, t_stages, samples)
        self.store_risk_matrices(risk_matrices)

        return super().save(*args, **kwargs)


    def delete(self, *args, **kwargs) -> None:
        """Delete the HDF5 file containing the risk matrices."""
        samples_path = Path(self.risk_matrices.path)
        self.risk_matrices.delete(save=False)
        samples_path.unlink(missing_ok=True)
        return super().delete(*args, **kwargs)

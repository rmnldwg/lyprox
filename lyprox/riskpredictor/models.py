"""
The model `TrainedLymphModel` holds an upload of parameter samples that were produced
during an inference run of the ``lymph-model``. The samples should be fetched from the
DVC remote storage and used to compute the prior risk matrices.

Given a specific diagnosis, as entered via the `forms.RiskForm`, the ``lymph-model``
package and the precomputed risk matrices in the `TrainedLymphModel` instances, the
personalized risk estimates can be computed.
"""
import io
from pathlib import Path

import h5py
import lyscripts
import numpy as np
import yaml
from django.db import models
from dvc.api import DVCFileSystem

from .. import loggers


def get_path_for_risk_matrices(instance, filename):
    """
    Returns the path where the risk matrices should be stored for a given
    `TrainedLymphModel` instance.
    """
    repo_path = instance.git_repo_url.split("//")[-1]
    return f"risk/{repo_path}/{instance.revision}.hdf5"


class TrainedLymphModel(loggers.ModelLoggerMixin, models.Model):
    """
    Model representing a trained probabilistic lymph node model as implemented in the
    ``lymph-model`` package.

    It fetches the HDF5 parameter samples from the DVC remote storage and uses them to
    compute the prior risk matrices and stores them in an HDF5 file, too.
    """
    git_repo_url = models.URLField(default="https://github.com/rmnldwg/lynference")
    """URL of the git repository that contains the trained model."""
    revision = models.CharField(max_length=40, default="main")
    """Git revision of the trained model. E.g., a commit hash, tag, or branch name."""
    samples_path = models.CharField(max_length=100, default="models/samples.hdf5")
    """Path to the HDF5 file containing the parameter samples inside the git repo."""
    params_path = models.CharField(max_length=100, default="params.yaml")
    """Path to the YAML file containing the model parameters inside the git repo."""
    risk_matrices = models.FileField(upload_to=get_path_for_risk_matrices)
    """HDF5 file containing the computed prior risk matrices."""
    num_samples = models.PositiveIntegerField(default=1000)
    """Number of samples to use for computing the prior risk matrices."""

    class Meta:
        unique_together = ("git_repo_url", "revision")

    def __str__(self):
        return f"{self.git_repo_url}/tree/{self.revision}"

    def save(self, *args, **kwargs) -> None:
        """Compute the risk matrices and store them in the HDF5 file."""
        fs = DVCFileSystem(url=self.git_repo_url, rev=self.revision)

        with fs.open(self.params_path) as params_file:
            params = yaml.safe_load(params_file)
            t_stages = params["model"]["t_stages"]

        with fs.open(self.samples_path) as samples_file:
            with h5py.File(samples_file, "r") as samples_h5:
                raw_chain = samples_h5["mcmc/chain"][:]
                num_dims = raw_chain.shape[-1]
                samples = raw_chain.reshape((-1, num_dims))
                rand_idx = np.random.choice(
                    samples.shape[0], size=self.num_samples, replace=False
                )
                samples = samples[rand_idx]

        self.logger.info("Loaded samples with dimensions %s", samples.shape)

        lymph_model = lyscripts.utils.create_model_from_config(params)
        risk_shape = lymph_model.risk(
            given_params=samples.mean(axis=0),
            t_stage=t_stages[0],
        ).shape

        self.logger.info("Created model %s", lymph_model)

        risk_matrices = {
            stage: np.empty(shape=(self.num_samples, *risk_shape)) for stage in t_stages
        }

        for i, sample in enumerate(samples):
            lymph_model.check_and_assign(sample)
            for stage in t_stages:
                risk_matrices[stage][i] = lymph_model.risk(t_stage=stage)

        self.logger.info("Computed risk matrices for T-categories %s", t_stages)

        # store risk matrices in HDF5 file
        bytes_io = io.BytesIO()
        with h5py.File(bytes_io, "w") as h5_file:
            for stage, risk_matrix in risk_matrices.items():
                h5_file.create_dataset(stage, data=risk_matrix)

        # store the HDF5 file in the `risk_matrices` field
        self.risk_matrices.save(
            get_path_for_risk_matrices(self, "_"), bytes_io, save=False
        )

        return super().save(*args, **kwargs)


    def delete(self, *args, **kwargs) -> None:
        """Delete the HDF5 file containing the risk matrices."""
        samples_path = Path(self.risk_matrices.path)
        self.risk_matrices.delete(save=False)
        samples_path.unlink()
        return super().delete(*args, **kwargs)

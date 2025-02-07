"""
Module for functions to predict the risk of lymphatic progression.

The code in this module is utilized by the `views.RiskPredictionView` of the
`riskpredictor` app to compute the risk of lymphatic progression for a given diagnosis.
"""

import logging

import numpy as np
from lydata.utils import ModalityConfig
from lymph.types import Model
from lyscripts.configs import DiagnosisConfig, add_modalities

logger = logging.getLogger(__name__)


def compute_posteriors(
    model: Model,
    priors: np.ndarray,
    diagnosis: DiagnosisConfig,
    specificity: float = 0.9,
    sensitivity: float = 0.9,
) -> np.ndarray:
    """Compute the posterior state dists for the given model, priors, and diagnosis."""
    modality_config = ModalityConfig(spec=specificity, sens=sensitivity)
    model = add_modalities(model=model, modalities={"diagnosis": modality_config})
    posteriors = []

    for prior in priors:
        posterior = model.posterior_state_dist(
            given_state_dist=prior,
            given_diagnosis=diagnosis,
        )
        posteriors.append(posterior)

    return np.stack(posteriors)

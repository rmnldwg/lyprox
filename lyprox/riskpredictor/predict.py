"""
Module for functions to predict the risk of lymphatic progression.

The code in this module is utilized by the `views.RiskPredictionView` of the
`riskpredictor` app to compute the risk of lymphatic progression for a given diagnosis.
"""

import logging
from collections import namedtuple
from typing import Any

import numpy as np
from lydata.utils import ModalityConfig
from lymph.models import HPVUnilateral, Unilateral
from lymph.types import Model
from lyscripts.configs import DiagnosisConfig, add_modalities

from lyprox.riskpredictor.models import CheckpointModel

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
    model = add_modalities(model=model, modalities={"D": modality_config})
    posteriors = []

    if isinstance(model, Unilateral | HPVUnilateral):
        diagnosis = diagnosis.ipsi
    else:
        diagnosis = diagnosis.model_dump()

    for prior in priors:
        posterior = model.posterior_state_dist(
            given_state_dist=prior,
            given_diagnosis=diagnosis,
        )
        posteriors.append(posterior)

    return np.stack(posteriors)


def assemble_diagnosis(
    form_data: dict[str, Any],
    lnls: list[str],
    modality: str = "D",
) -> DiagnosisConfig:
    """Create a `DiagnosisConfig` object from the cleaned form data."""
    diagnosis_dict = {}

    for side in ["ipsi", "contra"]:
        diagnosis_dict[side] = {modality: {}}
        for lnl in lnls:
            if f"{side}_{lnl}" not in form_data:
                continue
            diagnosis_dict[side][modality][lnl] = form_data[f"{side}_{lnl}"]

    return DiagnosisConfig(**diagnosis_dict)


MeanAndStd = namedtuple("MeanAndStd", ["mean", "std"])


def compute_risks(
    checkpoint: CheckpointModel,
    form_data: dict[str, Any],
    lnls: list[str],
) -> dict[str, MeanAndStd]:
    """Compute the risks for the given checkpoint and form data."""
    model = checkpoint.construct_model()
    priors = checkpoint.compute_priors(t_stage=form_data["t_stage"])
    diagnosis = assemble_diagnosis(form_data=form_data, lnls=lnls)

    posteriors = compute_posteriors(
        model=model,
        priors=priors,
        diagnosis=diagnosis,
        specificity=form_data["specificity"],
        sensitivity=form_data["sensitivity"],
    )

    risks = {}
    for side in ["ipsi", "contra"]:
        for lnl in lnls:
            if f"{side}_{lnl}" not in form_data:
                continue

            if isinstance(model, Unilateral | HPVUnilateral):
                involvement = {lnl: True}
            else:
                involvement = {side: {lnl: True}}

            _risks = [
                model.marginalize(involvement=involvement, given_state_dist=post)
                for post in posteriors
            ]
            risks[f"{side}_{lnl}"] = MeanAndStd(
                mean=np.mean(_risks),
                std=np.std(_risks),
            )

    return risks

"""
Module for functions to predict the risk of lymphatic progression.

The code in this module is utilized by the `views.RiskPredictionView` of the
`riskpredictor` app to compute the risk of lymphatic progression for a given diagnosis.
"""

import logging
import time
from typing import Any

import numpy as np
import pandas as pd
from lymph.models import Bilateral, Midline, Unilateral
from lyscripts.utils import flatten

from lyprox.riskpredictor.models import CheckpointModel

logger = logging.getLogger(__name__)


def create_patient(
    diagnosis: dict[str, dict[str, bool | None]],
    t_stage: str,
    is_bilateral: bool = False,
    midline_extension: bool | None = None,
) -> pd.DataFrame:
    """
    Create a patient dataframe from a specific diagnosis.

    This is necessary, so that the ``lymph-model`` can be used to compute the
    probability of the given diagnosis for any possible hidden state.
    """
    patient_row = {}

    if is_bilateral:
        patient_row["modality"] = diagnosis
        patient_row["info"] = {"tumor": {"t_stage": t_stage}}
        patient_row["info"]["tumor"]["midline_extension"] = midline_extension
    else:
        patient_row["modality"] = diagnosis["ipsi"]
        patient_row["info"] = {"t_stage": t_stage}

    patient_row = flatten(patient_row)
    return pd.DataFrame(patient_row, index=[0])


def compute_diagnose_probs(
    inference_result: CheckpointModel,
    t_stage: str,
    diagnosis: dict[str, dict[str, bool | None]],
    specificity: float,
    sensitivity: float,
    midline_extension: bool | None = None,
) -> dict[str, np.ndarray]:
    """
    Compute the probability of the selected diagnosis for any possible hidden state
    and for both sides of the neck, if the model is a bilateral one.

    In probabilistic terms, this is the probability P(D=d|X) of the diagnosis D=d given
    any of the possible hidden states X. Consequently, this is a 1D array of length
    2^V, where V is the number of LNLs in the model.
    """
    lymph_model = inference_result.get_lymph_model()
    lymph_model.modalities = {"modality": [specificity, sensitivity]}

    patient = create_patient(
        diagnosis,
        t_stage,
        is_bilateral=inference_result.is_bilateral,
        midline_extension=midline_extension,
    )
    lymph_model.patient_data = patient

    if inference_result.is_midline:
        model_selector = "ext" if midline_extension else "noext"
        lymph_model = getattr(lymph_model, model_selector)

    if inference_result.is_bilateral:
        return {
            "ipsi": lymph_model.ipsi.diagnose_matrices[t_stage],
            "contra": lymph_model.contra.diagnose_matrices[t_stage],
        }

    return {"ipsi": lymph_model.diagnose_matrices[t_stage]}


def compute_posterior_risks(
    inference_result: CheckpointModel,
    diagnose_probs: dict[str, np.ndarray],
    risk_matrices: np.ndarray,
) -> np.ndarray:
    """
    Compute the posterior risks for any possible hidden state and for each of
    the samples used to compute the prior risks.

    In probabilistic terms, this is the probability P(X|D=d) of any of the possible
    hidden state X given the diagnosis D=d. This is computed for each of the N samples.
    Consequently, this is a 3D array of shape (N, 2^V, 2^V) in the bilateral case, or
    (N, 2^V) in the unilateral case.
    """
    if inference_result.is_bilateral:
        posterior_risk = np.einsum(
            "i,nij,j->nij",
            diagnose_probs["ipsi"].flatten(),
            risk_matrices,
            diagnose_probs["contra"].flatten(),
        )
        normalization = np.sum(posterior_risk, axis=(1, 2)).reshape(-1, 1, 1)
    else:
        posterior_risk = np.einsum(
            "i,ni->ni",
            diagnose_probs["ipsi"].flatten(),
            risk_matrices,
        )
        normalization = np.sum(posterior_risk, axis=1).reshape(-1, 1)

    return posterior_risk / normalization


def create_marginalisation(
    lymph_model: Unilateral | Bilateral | Midline,
    pattern: dict[str, bool | None],
) -> np.ndarray:
    """
    Create a vector for marginalizing over hidden states that match given `pattern`.

    If one wants to know the probability of e.g. LNL II involvement, one needs to
    marginalize over all hidden states where LNL II is involved. This function creates
    a vector that is 1 for all hidden states that match the given `pattern` and 0 for
    all others.
    """
    if isinstance(lymph_model, Midline):
        lymph_model = lymph_model.ext

    if isinstance(lymph_model, Bilateral):
        lymph_model = lymph_model.ipsi

    pattern = np.array([pattern.get(lnl.name, None) for lnl in lymph_model.lnls])

    marginalisation = np.zeros(shape=len(lymph_model.state_list), dtype=bool)
    for i, state in enumerate(lymph_model.state_list):
        marginalisation[i] = np.all(
            np.equal(
                pattern,
                state,
                where=(pattern != None),  # noqa: E711
                out=np.ones_like(pattern, dtype=bool),
            )
        )

    return marginalisation


def compute_marginalised_risks(
    inference_result: CheckpointModel,
    posterior_risks: np.ndarray,
) -> dict[str, np.ndarray]:
    """
    Compute the marginalised risks of involvement of each LNL.

    In probabilistic terms, this is the probability P(X=x|D=d), which is computed by
    marginalizing over all hidden states that do match the given diagnosis (for wich
    the posterior risk over all possible hidden states was already computed).
    """
    num_lnls = len(inference_result.lnls)
    lymph_model = inference_result.get_lymph_model()
    marginalisation = np.ones(shape=(num_lnls, 2**num_lnls), dtype=bool)

    for i, lnl in enumerate(inference_result.lnls):
        marginalisation[i] = create_marginalisation(
            lymph_model,
            pattern={lnl: True},
        )

    marginalised_risks = {}
    if inference_result.is_bilateral:
        post_risks_marg_over_contra = np.sum(posterior_risks, axis=2).T
        post_risks_marg_over_ipsi = np.sum(posterior_risks, axis=1).T

        marginalised_risks["ipsi"] = marginalisation @ post_risks_marg_over_contra
        marginalised_risks["contra"] = marginalisation @ post_risks_marg_over_ipsi
    else:
        marginalised_risks["ipsi"] = marginalisation @ posterior_risks.T

    return marginalised_risks


def aggregate_results(
    inference_result: CheckpointModel,
    marginalized_risks: dict[str, np.ndarray],
) -> dict[str, list[float]]:
    """
    Aggregate the results of the risk computation into a dictionary.

    This is a helper function that is used to convert the numpy arrays that are
    returned by the risk computation into a dictionary that can be used as context
    for the `views.RiskPredictionView` view.

    The returned dictionary has the following structure: For each side (ipsi or contra)
    and each LNL, the dictionary contains a list of three values: The first value is
    the error of the prediction, the second value is the risk of involvement (but minus
    half the error), and the third value is the probability of being healthy (again
    minus half the error).
    """
    result = {}
    for side in ["ipsi", "contra"]:
        if side not in marginalized_risks:
            continue

        for i, lnl in enumerate(inference_result.lnls):
            risk_mean = 100 * np.mean(marginalized_risks[side][i])
            risk_stddev = 100 * np.std(marginalized_risks[side][i])
            result[f"{side}_{lnl}"] = [
                risk_stddev,  # error of the prediction
                risk_mean - risk_stddev / 2.0,  # risk of involvement - half error
                100.0 - (risk_mean - risk_stddev / 2.0),  # prob of healthy - half error
            ]

    return result


def risks(
    inference_result: CheckpointModel,
    t_stage: str,
    diagnosis: dict[str, dict[str, bool | None]],
    specificity: float,
    sensitivity: float,
    midline_extension: bool | None = None,
    **_kwargs,
) -> dict[str, Any]:
    """
    Compute the marginalized risk of microscopic involvement in any of the modelled
    LNLs for a given diagnosis.
    """
    start_time = time.perf_counter()

    diagnose_probs = compute_diagnose_probs(
        inference_result,
        t_stage,
        diagnosis,
        specificity,
        sensitivity,
        midline_extension,
    )
    risk_matrices = inference_result.load_risk_matrices(t_stage, midline_extension)

    posterior_risks = compute_posterior_risks(
        inference_result,
        diagnose_probs,
        risk_matrices,
    )

    marginalised_risks = compute_marginalised_risks(inference_result, posterior_risks)
    result = aggregate_results(inference_result, marginalised_risks)

    end_time = time.perf_counter()
    logger.info(f"Time elapsed: {end_time - start_time:.2f} seconds")

    return result


def default_risks(inference_result: CheckpointModel, **kwargs) -> dict[str, Any]:
    """Return default risks (everything unknown)."""
    result = {}
    for side in ["ipsi", "contra"]:
        for lnl in inference_result.lnls:
            result[f"{side}_{lnl}"] = [100, 0, 0]

    return result

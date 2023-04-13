"""
Module for functions to predict the risk of lymphatic progression.

The code in this module is utilized by the `views.RiskPredictionView` of the
`riskpredictor` app to compute the risk of lymphatic progression for a given diagnosis.
"""
import logging
import time
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np
import pandas as pd
from lymph import Bilateral, MidlineBilateral, Unilateral
from lyscripts.utils import flatten, model_from_config

from .models import TrainedLymphModel

logger = logging.getLogger(__name__)


def create_patient(
    diagnosis: Dict[str, Dict[str, Optional[bool]]],
    t_stage: str,
    is_bilateral: bool = False,
    midline_extension: Optional[bool] = None,
) -> pd.DataFrame:
    """Create a patient dataframe from a specific diagnosis.

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
    trained_lymph_model: TrainedLymphModel,
    t_stage: str,
    diagnosis: Dict[str, Dict[str, Optional[bool]]],
    specificity: float,
    sensitivity: float,
    midline_extension: Optional[bool] = None,
) -> Tuple[Dict[str, np.ndarray], Union[Unilateral, Bilateral, MidlineBilateral]]:
    """Compute the probability of the selected diagnosis for any possible hidden state
    and for both sides of the neck, if the model is a bilateral one.

    In probabilistic terms, this is the probability P(D=d|X) of the diagnosis D=d given
    any of the possible hidden states X. Consequently, this is a 1D array of length
    2^V, where V is the number of LNLs in the model.

    Note that the ``trained_lymph_model`` object is an instance of the
    `models.TrainedLymphModel` Django model, while the ``helper_lymph_model`` that is
    being created here is an instance of the classes from the ``lymph-model`` package.

    This function also returns the ``helper_lymph_model`` object.
    """
    helper_lymph_model = model_from_config(
        graph_params=trained_lymph_model.params["graph"],
        model_params=trained_lymph_model.params["model"],
    )
    helper_lymph_model.modalities = {"modality": [specificity, sensitivity]}

    patient = create_patient(
        diagnosis, t_stage,
        is_bilateral=trained_lymph_model.is_bilateral,
        midline_extension=midline_extension,
    )
    helper_lymph_model.patient_data = patient

    if trained_lymph_model.is_midline:
        model_selector = "ext" if midline_extension else "noext"
        helper_lymph_model = getattr(helper_lymph_model, model_selector)

    if trained_lymph_model.is_bilateral:
        return {
            "ipsi": helper_lymph_model.ipsi.diagnose_matrices[t_stage],
            "contra": helper_lymph_model.contra.diagnose_matrices[t_stage],
        }, helper_lymph_model

    return {"ipsi": helper_lymph_model.diagnose_matrices[t_stage]}, helper_lymph_model


def compute_posterior_risks(
    trained_lymph_model: TrainedLymphModel,
    diagnose_probs: Dict[str, np.ndarray],
    risk_matrices: np.ndarray,
) -> np.ndarray:
    """Compute the posterior risks for any possible hidden state and for each of
    the samples used to compute the prior risks.

    In probabilistic terms, this is the probability P(X|D=d) of any of the possible
    hidden state X given the diagnosis D=d. This is computed for each of the N samples.
    Consequently, this is a 3D array of shape (N, 2^V, 2^V) in the bilateral case, or
    (N, 2^V) in the unilateral case.
    """
    if trained_lymph_model.is_bilateral:
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
    helper_lymph_model: Union[Unilateral, Bilateral, MidlineBilateral],
    pattern: Dict[str, Optional[bool]],
) -> np.ndarray:
    """Create a vector for marginalizing over hidden states that match the given
    pattern.

    If one wants to know the probability of e.g. LNL II involvement, one needs to
    marginalize over all hidden states where LNL II is involved. This function creates
    a vector that is 1 for all hidden states that match the given pattern and 0 for
    all others.
    """
    if isinstance(helper_lymph_model, MidlineBilateral):
        helper_lymph_model = helper_lymph_model.ext

    if isinstance(helper_lymph_model, Bilateral):
        helper_lymph_model = helper_lymph_model.ipsi

    pattern = np.array([pattern.get(lnl.name, None) for lnl in helper_lymph_model.lnls])

    marginalisation = np.zeros(shape=len(helper_lymph_model.state_list), dtype=bool)
    for i, state in enumerate(helper_lymph_model.state_list):
        marginalisation[i] = np.all(np.equal(
            pattern, state,
            where=(pattern != None),
            out=np.ones_like(pattern, dtype=bool),
        ))

    return marginalisation


def compute_marginalised_risks(
    trained_lymph_model: TrainedLymphModel,
    helper_lymph_model: Union[Unilateral, Bilateral, MidlineBilateral],
    posterior_risks: np.ndarray,
) -> Dict[str, np.ndarray]:
    """Compute the marginalised risks of involvement of each LNL.

    In probabilistic terms, this is the probability P(X=x|D=d), which is computed by
    marginalizing over all hidden states that do match the given diagnosis (for wich
    the posterior risk over all possible hidden states was already computed).
    """
    num_lnls = len(trained_lymph_model.lnls)
    marginalisation = np.ones(shape=(num_lnls, 2**num_lnls), dtype=bool)

    for i, lnl in enumerate(trained_lymph_model.lnls):
        marginalisation[i] = create_marginalisation(
            helper_lymph_model,
            pattern={lnl: True},
        )

    marginalised_risks = {}
    if trained_lymph_model.is_bilateral:
        post_risks_marg_over_contra = np.sum(posterior_risks, axis=2).T
        post_risks_marg_over_ipsi = np.sum(posterior_risks, axis=1).T

        marginalised_risks["ipsi"] = marginalisation @ post_risks_marg_over_contra
        marginalised_risks["contra"] = marginalisation @ post_risks_marg_over_ipsi
    else:
        marginalised_risks["ipsi"] = marginalisation @ posterior_risks.T

    return marginalised_risks


def aggregate_results(
    trained_lymph_model: TrainedLymphModel,
    marginalized_risks: Dict[str, np.ndarray],
) -> Dict[str, Any]:
    """Aggregate the results of the risk computation into a dictionary.

    This is a helper function that is used to convert the numpy arrays that are
    returned by the risk computation into a dictionary that can be used as context
    for the `views.RiskPredictionView` view.
    """
    result = {}
    for side in ["ipsi", "contra"]:
        if side not in marginalized_risks:
            continue

        for i, lnl in enumerate(trained_lymph_model.lnls):
            lnl_risk = 100 * np.mean(marginalized_risks[side][i])
            result[f"{side}_{lnl}"] = [0, lnl_risk, 100. - lnl_risk]

    return result


def risks(
    trained_lymph_model: TrainedLymphModel,
    t_stage: str,
    diagnosis: Dict[str, Dict[str, Optional[bool]]],
    specificity: float,
    sensitivity: float,
    midline_extension: Optional[bool] = None,
    **_kwargs,
) -> Dict[str, Any]:
    """Compute the marginalized risk of microscopic involvement in any of the modelled
    LNLs for a given diagnosis.
    """
    start_time = time.perf_counter()

    diagnose_probs, helper_lymph_model = compute_diagnose_probs(
        trained_lymph_model,
        t_stage,
        diagnosis,
        specificity,
        sensitivity,
        midline_extension,
    )
    risk_matrices = trained_lymph_model.load_risk_matrices(t_stage, midline_extension)

    posterior_risks = compute_posterior_risks(
        trained_lymph_model,
        diagnose_probs,
        risk_matrices,
    )

    marginalised_risks = compute_marginalised_risks(
        trained_lymph_model,
        helper_lymph_model,
        posterior_risks,
    )

    result = aggregate_results(trained_lymph_model, marginalised_risks)

    end_time = time.perf_counter()
    logger.info(f"Time elapsed: {end_time - start_time:.2f} seconds")

    return result


def default_risks(trained_lymph_model: TrainedLymphModel, **kwargs) -> Dict[str, Any]:
    """Return default risks (everything unknown)."""
    result = {}
    for side in ["ipsi", "contra"]:
        for lnl in trained_lymph_model.lnls:
            result[f"{side}_{lnl}"] = [100, 0, 0]

    return result

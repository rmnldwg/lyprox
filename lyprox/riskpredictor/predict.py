"""
Module for functions to predict the risk of lymphatic progression.

The code in this module is utilized by the `views.RiskPredictionView` of the
`riskpredictor` app to compute the risk of lymphatic progression for a given diagnosis.
"""
import logging
import time
from typing import Any, Dict, Optional, Union

import pandas as pd
from lyscripts.utils import flatten, model_from_config

from .models import TrainedLymphModel

logger = logging.getLogger(__name__)


def create_patient(
    diagnosis: Dict[str, Dict[str, Optional[bool]]],
    t_stage: Union[str, int],
    is_bilateral: bool = False,
    midline_extension: Optional[bool] = None,
) -> pd.DataFrame:
    """Create a patient dataframe from a diagnosis and a T-stage.

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


def risks(
    trained_lymph_model: TrainedLymphModel,
    t_stage: Union[str, int],
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

    # In contrast to the `trained_lymph_model` object, the `helper_lymph_model` is
    # an instance from the `lymph-model` package. This represents the underlying
    # probabilistic model.

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

    result = produce_dummy_result(trained_lymph_model)
    logger.info(result)

    end_time = time.perf_counter()
    logger.info(f"Time elapsed: {end_time - start_time:.2f} seconds")
    return result


def produce_dummy_result(trained_lymph_model):
    result = {}
    for side in ["ipsi", "contra"]:
        for lnl in trained_lymph_model.lnls:
            result[f"{side}_{lnl}"] = [1,2,3]
    return result

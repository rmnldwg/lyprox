"""Risk predictions for involvement patterns, given personalized diagnoses.

The predictions displayed in the risk predictor are not actually computed by the web
app. Instead, LyProX reconstructs one of the `lymph.models` with the help of config
files - parsed by the `lyscripts`_ package - that can be found in any repos that define
a `DVC`_ pipeline.

This is probably the most complex interplay between the different libraries, so we will
try to break it down as complrehensively as possible:

1. The `lymph`_ Models
    The code implementing the mathematical models for lymphatic tumor progression are
    provided by the `lymph`_ library. They implement the different `lymph.models`.
2. `DVC`_ Pipelines in Paper Repos
    Our research group has, in the past, published a number of papers where we inferred
    the optimal parameters of various such models, given a cohort of patients. These
    sets of inferred parameter samples are referenced by a tool called `DVC`_ in
    different repositories with instructions on how to fetch them from a remote storage
    container.
3. Reproducing Models with `lyscripts`_
    However, these references are worthless without unambiguous instructions on how to
    reconstruct the exact model that was used for inference. For this, we use the
    `lyscripts`_ package. Its module `lyscripts.configs` provides a bunch of
    `pydantic.BaseModel` subclasses for defining basically every important aspect of the
    modelling process.

What happens in this "little" app now, is that one defines where it should look for
the YAML files that define a model and a sampling pipeline. This definition is stored
as a `CheckpointModel` in the `SQLite`_ database. From instances of this class, one
can then validate the config files, fetch the samples from the remote storage using
`DVC`_, and precompute prior state distributions from the trained model. See the docs
of the `CheckpointModel` for a list of all the available methods and how they cache
their intermediate results using `joblib`.

Consequently, a user can then head to the risk predictor's dashboard, select a
`CheckpointModel` and have the web app compute specific risks defined via the
`RiskpredictorForm` from the precomputed quantities. This actual risk predictions
happens in the `predict` module of the app.

.. _lymph: https://lymph-model.readthedocs.io/stable
.. _DVC: https://dvc.org/
.. _lyscripts: https://lyscripts.readthedocs.io/latest
.. _SQLite: https://www.sqlite.org/index.html
"""

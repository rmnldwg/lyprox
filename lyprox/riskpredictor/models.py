"""
The model `TrainedLymphModel` holds an upload of parameter samples that were produced
during an inference run of the ``lymph-model``. The samples are stored in an HDF5 file
and used to pre-compute the risk matrices for each of the stored samples.

Given a specific diagnosis, as entered via the `forms.RiskForm`, the ``lymph-model``
package and the precomputed risk matrices in the `TrainedLymphModel` instances, the
personalized risk estimates can be computed.
"""

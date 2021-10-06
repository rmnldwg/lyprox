.. module:: patients.mixins


======
Mixins
======

For the patient model, I wrote only two mixins. But those are rather 
security-relevant as they make sure only users can edit patients, tumors and 
diagnoses when they come from the same institution as said patients, tumors and 
diagnoses.

.. autoclass:: patients.mixins.InstitutionCheckPatientMixin
    :members:
    :show-inheritance:

.. autoclass:: patients.mixins.InstitutionCheckObjectMixin
    :members:
    :show-inheritance:
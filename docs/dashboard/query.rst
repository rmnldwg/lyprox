.. module:: dashboard.query

========
Querying
========

Here is where the magic happens. All the functions that are called in the 
:ref:`dashboard-view` one after the other are defined here.

First there are some helper functions that hanlde all the different types of 
data before the actual querying can be done.


Helpers
-------

.. autofunction:: dashboard.query.tf2arr

.. autofunction:: dashboard.query.subsite2arr

.. autofunction:: dashboard.query.side2arr


Query functions
---------------

.. autofunction:: dashboard.query.patient_specific

.. autofunction:: dashboard.query.tumor_specific

.. autofunction:: dashboard.query.diagnose_specific

.. autofunction:: dashboard.query.n_zero_specific
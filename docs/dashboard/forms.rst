.. module:: dashboard.forms

====
Form
====

This form is one of the more handmade parts of the interface, since it cannot 
be constructed automatically from an existing model. Here we define the 
selection criteria which the user can apply to narrow down the database to the 
subset of their interest and explore correlations between occurence of 
metastases in lymph node levels.

The first class described here defines a toggle button that has three states. 
One indicates that only patients should be included in the subset that have the 
respective characteristic, the other one includes only patients that do not 
exhibit that detail and the default state (usually in the middle) just tells 
the query to ignore that feature and perform no selection based on it.

.. autoclass:: dashboard.forms.ThreeWayToggle
    :members:
    :show-inheritance:

.. autoclass:: dashboard.forms.DashboardForm
    :members:
    :show-inheritance:

It is also possible to choose from which institution(s) data should be 
displayed. This is achieved by customizing Django's class 
:class:`ModelMultipleChoiceField` and adding the property ``names_and_urls`` to 
it, so that one can access the name and logo URL of the institutions for 
nicer visuals.

.. autoclass:: dashboard.forms.InstitutionMultipleChoiceField
    :members:
    :show-inheritance:

.. autoclass:: dashboard.forms.InstitutionModelChoiceIndexer
    :members:
    :show-inheritance:
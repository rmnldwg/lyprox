.. module:: patients.filters

=======
Filters
=======

Actually, I only use one filter for displaying a filterable list of patients. 
The ability to create a filter from a model and have that filter sort of 
automatically create a form for you is provided by a third-party extension to 
django called `django-filter <https://django-filter.readthedocs.io/en/stable/>`_.


.. autoclass:: patients.filters.PatientFilter
    :members:
    :show-inheritance:
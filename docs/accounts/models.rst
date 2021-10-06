.. module:: accounts.models

======
Models
======

Here we document how we have adapted the default implementation of a user and 
user management system by Django. As mentioned, some of the main changes are 
related to the additional (and also documented) institution class.

User
----

.. autoclass:: accounts.models.User
    :members:
    :show-inheritance:

.. autoclass:: accounts.models.UserManager
    :members:
    :show-inheritance:

Institution
-----------

.. autoclass:: accounts.models.Institution
    :members:
    :show-inheritance:

.. autoclass:: accounts.models.CountryField
    :members:
    :show-inheritance:
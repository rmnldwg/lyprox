==================================
User Management and Authentication
==================================

In this section the management and authentication of users in our interface 
will be highlighted. Overall, it is pretty close to the stock implementation 
of a user in Django, but we made some modifications in order ot account for 
institutions. A user is probably in most cases a researcher who is affiliated 
with a respective institution that may also provide parts of the data that is 
ultimately displayed here, so it is necessary to capture this in both the 
user's and the patient's models.

.. toctree::
    :maxdepth: 2

    accounts/models
    accounts/forms
    accounts/views

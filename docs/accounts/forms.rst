.. module:: accounts.forms

=====
Forms
=====

Here we only use a slightly modified version of the default login form. The 
:class:`SignupRequestForm` isn't used so far and if it ever will be the idea is 
only to generate an automatic email to the admin from the fields that have been 
filled, so that the admin can then create the user.

.. autoclass:: accounts.forms.CustomAuthenticationForm
    :members:
    :show-inheritance:

.. autoclass:: accounts.forms.SignupRequestForm
    :members:
    :show-inheritance:
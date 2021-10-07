.. module:: dashboard.views

.. _dashboard-view:

====
View
====

The most complex view in the whole interface is this one. It handles to complex 
:class:`forms.DashboardForm` and delegates the different parts of the query, 
based on the selections in said form, to special querying functions. In the end 
it creates and returns the statistics and numbers that are then shown as 
numbers and bar plots in the actual dashboard.

Technically, it is a subclass of the generic :class:`ListView`, since that has 
already a method :meth:`get_queryset` that can be overriden. This also allows 
us to add a button to the dashboard interface that redirects to a list view of 
the patients selected in via all the toggle buttons.

.. autoclass:: dashboard.views.DashboardView
    :members:
    :show-inheritance:
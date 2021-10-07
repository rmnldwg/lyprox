=========
Dashboard
=========

Here we document the core part of our interface: The dashboard. It visualizes 
all the data we have collected in an intuitive and meaningful way that we hope 
benefits many researchers on the field of head & neck cancer and shows the 
importance and usefulness of sharing data in as much detail as possible.

The most complex part about the implementation of the dashboard lies in the 
database queries and the way the numbers are computed from the resutling query. 
Below, one can find our documentation is hopefully enough detail to make clear 
how this works.

.. toctree::
    :maxdepth: 2

    dashboard/forms
    dashboard/views
    dashboard/query
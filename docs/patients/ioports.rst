.. module:: patients.ioports

=======================
Importing and Exporting
=======================

To be able to parse a CSV file first into a :class:`pandas.DataFrame` and then 
into actual database entries, I wrote a couple of classes and functions 
separately. Similarily, there is some code written to do the reverse, namely 
creating first a :class:`pandas.DataFrame` and then a CSV file from the SQL 
database I use.

.. autoclass:: patients.ioports.ParsingError
    :mambers:
    :show-inheritance:

.. autofunction:: patients.ioports.compute_hash

.. autofunction:: patients.ioports.nan_to_None

.. autofunction:: patients.ioports.get_model_fields

.. autofunction:: patients.ioports.row2patient

.. autofunction:: patients.ioports.row2tumors

.. autofunction:: patients.ioports.row2diagnoses

.. autofunction:: patients.ioports.import_from_pandas

.. autofunction:: patients.ioports.export_to_pandas
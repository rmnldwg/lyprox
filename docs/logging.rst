.. module:: core.loggers

=======
Logging
=======

To provide some basic and easy to use logging capabilities, we implemented some 
logging classes for ``Models``, ``Forms`` and class-based ``Views``. That 
automatically log certain actions that are typical for the respective class. 
For example, a model class that inherits from our 
:class:`core.loggers.ModelLoggerMixin` automatically provides logging for the 
:meth:`save()` and :meth:`delete()` methods of the :class:`Model` class.


.. autoclass:: core.loggers.ModelLoggerMixin
    :members:
    :show-inheritance:

.. autoclass:: core.loggers.FormLoggerMixin
    :members:
    :show-inheritance:

.. autoclass:: core.loggers.ViewLoggerMixin
    :members:
    :show-inheritance:
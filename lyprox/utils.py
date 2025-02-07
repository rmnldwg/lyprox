"""Utility functions."""

import logging
from typing import Any, TypeVar

from django.forms import Form

logger = logging.getLogger(__name__)

T = TypeVar("FormT", bound=Form)


def form_from_initial(cls: type[T], **kwargs: Any) -> T:
    """
    Create a form instance with the defined initial data.

    Form fields are typically defined with initial values. And Django's forms allow
    extracting this initial values from an instance of a form. So, what this helper
    function does is inspect all fields of a form, extract the initial values, and
    then creates a new form instance with these initial values.

    Any additional keyword arguments are directly passed to the form constructor.
    """
    form = cls(**kwargs)
    initial_data = {}
    for name, field in form.fields.items():
        initial_data[name] = form.get_initial_for_field(field, name)

    logger.info(f"Creating {cls.__name__} form with initial data.")
    logger.debug(f"{initial_data = }")
    return cls(initial=initial_data, **kwargs)

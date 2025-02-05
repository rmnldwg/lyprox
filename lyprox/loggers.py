"""Mixins that provide automatic logging capabilities for models, forms and views."""

import logging


class ModelLoggerMixin:
    """
    Mixin for django models that provide logging capabilities.

    Any model class that (also) inherits from this mixin will automatically create
    logs for some important events, such as saving and deleting instances.
    """

    @property
    def logger(self):
        """Return the right logger for the class."""
        name = ".".join([self.__module__, self.__class__.__name__])
        return logging.getLogger(name)

    def save(self, *args, **kwargs):
        """Log information about the instance when saving."""
        res = super().save(*args, **kwargs)
        self.logger.info(f"Saved {self.__class__.__name__} <{self}>")
        return res

    def delete(self, *args, **kwargs):
        """Log information about the instance when deleting."""
        res = super().delete(*args, **kwargs)
        self.logger.info(f"Deleting {self.__class__.__name__} <{self}>")
        return res


class FormLoggerMixin:
    """
    Mixin for django forms that provide logging information for events.

    Adding this mixin to the classes a form inherits from will automatically enable
    logging some information when the form is validated.
    """

    @property
    def logger(self):
        """Return the right logger for the class."""
        name = ".".join([self.__module__, self.__class__.__name__])
        return logging.getLogger(name)

    def is_valid(self) -> bool:
        """Perform the validation as usual and log the result."""
        if super().is_valid():
            self.logger.info("Form successfully cleaned.")
            self.logger.debug(f"Form cleaned data: {self.cleaned_data}")
            return True

        if self.errors:
            self.logger.warning(self.errors.as_data())
        else:
            self.logger.info("Form has errors (or is unbound).")

        return False


class ViewLoggerMixin:
    """
    Mixin for django views that provides logging capabilities.

    As the `FormLoggerMixin`, this mixin provides logging information for events, but
    in views instead of forms.

    This is not too useful anymore, as most class-based views have been replaced by
    function-based views.
    """

    action = None

    @property
    def logger(self):
        """Return the right logger for the class."""
        name = ".".join([self.__module__, self.__class__.__name__])
        return logging.getLogger(name)

    def form_valid(self, form):
        """Log the successful validation of the form."""
        ret = super().form_valid(form)
        msg = f"{self.object.__class__.__name__} <{self.object}> successfully saved."
        self.logger.info(msg)
        return ret

    def form_invalid(self, form):
        """Log the failed validation of the form."""
        msg = f"Form {form.__class__.__name__} invalid."
        self.logger.info(msg)
        return super().form_invalid(form)

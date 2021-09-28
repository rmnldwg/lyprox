import logging
import time
from typing import Dict, Any


class ModeLoggerMixin(object):
    """Mixin for django models that provide logging capabilities."""
    
    @property
    def logger(self):
        name = '.'.join([
            self.__module__,
            self.__class__.__name__
        ])
        return logging.getLogger(name)
    
    def save(self, *args, **kwargs):
        self.logger.info(f"Saving {self.__class__.__name__} <{self}>")
        return super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        self.logger.info(f"Deleting {self.__class__.__name__} <{self}>")
        return super().delete(*args, **kwargs)


class FormLoggerMixin(object):
    """Mixin for django forms that provide logging information for events like 
    successfull/failed validation."""
    
    @property
    def logger(self):
        name = '.'.join([
            self.__module__,
            self.__class__.__name__
        ])
        return logging.getLogger(name)
    
    
    def is_valid(self) -> bool:
        if super().is_valid():
            msg = f"Form successfully cleaned."
            self.logger.info(msg)
            return True
        
        else:
            msg = f"Form has errors (or is unbound)."
            self.logger.info(msg)
            return False


class ViewLoggerMixin(object):
    """Mixin for django views that provides logging capabilities."""
    action = None
    
    @property
    def logger(self):
        name = '.'.join([
            self.__module__,
            self.__class__.__name__
        ])
        return logging.getLogger(name)

    def form_valid(self, form):
        ret = super().form_valid(form)
        msg = f"{self.object.__class__.__name__} <{self.object}> successfully saved."
        self.logger.info(msg)
        return ret
    
    def form_invalid(self, form):
        msg = f"Form {form.__class__.__name__} invalid."
        self.logger.info(msg)
        return super().form_invalid(form)
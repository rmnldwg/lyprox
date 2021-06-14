import logging
from typing import Dict, Any


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
        msg = f"{self.object.__class__.__name__} ({self.object}) has been saved."
        self.logger.info(msg)
        return ret
    
    def form_invalid(self, form):
        msg = f"Form {form} invalid."
        self.logger.info(msg)
        return super().form_invalid(form)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        msg = f"{instance.__class__.__name__} ({instance}) has been deleted."
        res = super().delete(request, *args, **kwargs)
        self.logger.info(msg)
        return res

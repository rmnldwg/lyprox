import logging


class ModelLoggerMixin(object):
    """Mixin for django models that provide logging capabilities for typical 
    actions and operations performed with models."""
    
    @property
    def logger(self):
        """Return a logger with the correct name, depending on the class it is 
        used for."""
        name = '.'.join([
            self.__module__,
            self.__class__.__name__
        ])
        return logging.getLogger(name)
    
    def save(self, *args, **kwargs):
        """Log the saving of an instance."""
        self.logger.info(f"Saving {self.__class__.__name__} <{self}>")
        return super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Log the deletion of an instance."""
        self.logger.info(f"Deleting {self.__class__.__name__} <{self}>")
        return super().delete(*args, **kwargs)


class FormLoggerMixin(object):
    """Mixin for django forms that provide logging information for events like 
    successfull/failed validation."""
    
    @property
    def logger(self):
        """Return a logger with the correct name, depending on the class it is 
        used for."""
        name = '.'.join([
            self.__module__,
            self.__class__.__name__
        ])
        return logging.getLogger(name)
    
    
    def is_valid(self) -> bool:
        """Log successful/failed validation of form."""
        if super().is_valid():
            msg = f"Form successfully cleaned."
            self.logger.info(msg)
            return True
        
        else:
            msg = f"Form has errors (or is unbound)."
            self.logger.info(msg)
            return False


class ViewLoggerMixin(object):
    """Mixin for django views that provides logging capabilities for views that 
    create or edit model instances."""
    action = None
    
    @property
    def logger(self):
        name = '.'.join([
            self.__module__,
            self.__class__.__name__
        ])
        return logging.getLogger(name)

    def form_valid(self, form):
        """Log the form validation that leads to saving the model instance."""
        ret = super().form_valid(form)
        msg = f"{self.object.__class__.__name__} <{self.object}> successfully saved."
        self.logger.info(msg)
        return ret
    
    def form_invalid(self, form):
        """Log if a form cannot be validated to change a model's instance."""
        msg = f"Form {form.__class__.__name__} invalid."
        self.logger.info(msg)
        return super().form_invalid(form)
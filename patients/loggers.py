import logging


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


    def get_success_url(self) -> str:
        msg = f"Successfully performed action {self.action}"
        self.logger.info(msg)
        return super(ViewLoggerMixin, self).get_success_url()
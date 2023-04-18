"""
Here we define custom model fields that add some functionality to the existing Django
model fields.
"""
from dateutil.parser import ParserError, parse
from django.db import models


class RobustDateField(models.DateField):
    """
    DateField that doesn't raise a ValidationError when the date string isn't
    formated according to ISO (YYYY-MM-DD)
    """
    def to_python(self, value):
        if isinstance(value, str):
            try:
                value = parse(value).date()
            except ParserError:
                return None

        return super().to_python(value)

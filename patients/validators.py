"""
This module contains validators for model and form fields. Most imprtantly, the
`FileTypeValidator` for checking the actual file type of an uploaded file is defined
here.
"""

import magic

from django.forms import ValidationError
from django.utils.deconstruct import deconstructible
from django.template.defaultfilters import filesizeformat


@deconstructible
class FileTypeValidator:
    """
    Validator that checks the size and content of a file using the ``magic`` library.
    """
    error_messages = {
        "max_size": (
            "The maximum file size is %(max_size)s, "
            "but this file's size is %(data_size)s."
        ),
        "file_types": (
            "The only allowed file type is 'CSV text', not %(data_type)s"
        )
    }

    def __init__(self, max_size=None, file_types=()) -> None:
        self.max_size = max_size
        self.file_types = file_types

    def __call__(self, data):
        if self.max_size is not None and data.size > self.max_size:
            params = {
                "max_size": filesizeformat(self.max_size),
                "data_size": filesizeformat(data.size),
            }
            raise ValidationError(self.error_messages["max_size"], 'max_size', params)

        if self.file_types:
            if not data.readable() or data.mode != "rb":
                data.open(mode="rb")
            data_type = magic.from_buffer(data.read(), mime=True)
            data.close()

            if data_type not in self.file_types:
                params = {
                    "data_type": data_type
                }
                raise ValidationError(
                    self.error_messages["file_types"], "file_types", params
                )

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, FileTypeValidator) and
            self.max_size == other.max_size and
            self.file_types == other.file_types
        )

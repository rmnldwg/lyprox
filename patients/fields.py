"""
Here we define custom model fields that add some functionality to the existing Django
model fields.
"""
import hashlib
import logging

from dateutil.parser import ParserError, parse
from django.db import models
from django.db.models.fields.files import FieldFile

logger = logging.getLogger(name=__name__)


class CorruptedFileError(Exception):
    """
    Raised when `FieldFileWithHash` notices a file has been changed after its hash
    has been computed and fixed.
    """

class DuplicateFileError(Exception):
    """
    Exception raised when e.g. during uploading or saving the `Dataset` model notices
    a new file is already stored in one of the other datasets.
    """


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


class FieldFileWithHash(FieldFile):
    """
    ``FieldFile`` that adds an MD5 hash value as the property `md5_hash` to its
    defintion which in turn allows me to detect and block changes to the file and/or
    the dataset using that hash value.
    """
    def __init__(self, instance, field, name) -> None:
        super().__init__(instance, field, name)
        self._md5_hash = None

    @property
    def md5_hash(self):
        """
        Return the MD5 hash of the associated file. This method also checks if the
        file was changed and raises an error if that is the case.
        """
        self._require_file()

        if not self.file.readable() or self.file.mode != "rb":
            self.file.open(mode="rb")

        file_content = self.file.read()
        computed_hash = hashlib.md5(file_content).hexdigest()
        self.file.close()

        if getattr(self, "_md5_hash", None) is None:
            self._md5_hash = computed_hash
        elif self._md5_hash != computed_hash:
            raise CorruptedFileError("Stored hash does not match hash of stored file.")

        return self._md5_hash


class FileFieldWithHash(models.FileField):
    """
    A normal ``FileField`` that uses my custom `FieldFileWithHash` instead of Django's
    built-in ``FieldFile``.
    """
    attr_class = FieldFileWithHash

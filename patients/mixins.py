"""
Here we define some mixins that add functionality to the patient-related objects. So
far, this consists only of a mixin that blocks saving or deleting a `Patient`, `Tumor`
or `Diagnose` if the associated `Dataset` is locked.
"""
# pylint: disable=no-member

import patients.models as models


class LockedDatasetMixin:
    """
    Mixin for the `Patient`, `Tumor` and `Diagnose` classes to block any editing or
    deletion attempts when the `Dataset` they belong to is locked.
    """
    @property
    def _must_raise(self):
        """Infer from class if an error should be raised on save/delete."""
        if isinstance(self, models.Patient):
            return self.dataset.is_locked
        elif isinstance(self, (models.Tumor, models.Diagnose)):
            return self.patient.dataset.is_locked

    def save(self, *args, **kwargs):
        """Raise `LockedDatasetError` before saving if associated dataset is locked."""
        if self._must_raise:
            raise models.LockedDatasetError(
                f"Cannot edit/save {self.__class__.__name__} that is associated "
                "with a locked dataset"
            )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Raise `LockedDatasetError` befor deleting if associated dataset is locked."""
        if self._must_raise:
            raise models.LockedDatasetError(
                f"Cannot delete {self.__class__.__name__} that is associated "
                "with a locked dataset"
            )
        return super().delete(*args, **kwargs)

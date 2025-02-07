"""Boilerplate code to register the CheckpointModel with the Django admin interface."""

from django.contrib import admin

from .models import CheckpointModel

# Register your models here.
admin.site.register(CheckpointModel)

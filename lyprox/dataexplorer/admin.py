"""Register the models for the admin interface."""

from django.contrib import admin

from lyprox.dataexplorer.models import DatasetModel

admin.site.register(DatasetModel)

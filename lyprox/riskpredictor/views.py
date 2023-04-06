"""
Module for the views of the riskpredictor app.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView

from ..loggers import ViewLoggerMixin
from .forms import TrainedLymphModelForm
from .models import TrainedLymphModel


class AddTrainedLymphModelView(
    ViewLoggerMixin,
    LoginRequiredMixin,
    CreateView,
):
    """View for adding a new `TrainedLymphModel` instance."""
    model = TrainedLymphModel
    form_class = TrainedLymphModelForm
    template_name = "riskpredictor/trainedlymphmodel_form.html"
    success_url = "/riskpredictor/dashboard/"

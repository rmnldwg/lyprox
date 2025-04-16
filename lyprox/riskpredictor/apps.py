"""Boilerplate Django configuration for the riskpredictor app."""

from django.apps import AppConfig


class RiskConfig(AppConfig):
    """Django configuration for the riskpredictor app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "lyprox.riskpredictor"
    add_to_navbar = True

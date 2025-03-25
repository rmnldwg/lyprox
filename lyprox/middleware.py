"""Middlewares intercept and modify requests before handling them.

That may be useful if one wants to redirect a user in specific situation. For example,
if the website is in maintenance mode, the `MaintenanceMiddleware` will redirect all
requests to the maintenance page.
"""

import logging
import re

from django import urls
from django.shortcuts import redirect

from lyprox import settings

logger = logging.getLogger(__name__)


class MaintenanceMiddleware:
    """Redirect maintenance page if the ``MAINTENANCE`` setting is ``True``."""

    def __init__(self, get_response) -> None:
        """Create the middleware."""
        self.get_response = get_response

    def __call__(self, request):
        """Process the request."""
        path = request.META.get("PATH_INFO", "")

        if settings.MAINTENANCE and not path == urls.reverse("maintenance"):
            return redirect(urls.reverse("maintenance"))

        return self.get_response(request)


class LoginRequiredMiddleware:
    """Redirect to login if requested URL matches one of the ``LOGIN_REQUIRED_URLS``.

    This code is adapted from `stackoverflow`_.

    .. _stackoverflow: https://stackoverflow.com/questions/2164069/best-way-to-make-djangos-login-required-the-default
    """

    def __init__(self, get_response) -> None:
        """Create the middleware."""
        self.get_response = get_response
        self.login_required_urls = tuple(
            re.compile(url) for url in settings.LOGIN_REQUIRED_URLS
        )
        self.login_not_required_urls = tuple(
            re.compile(url) for url in settings.LOGIN_NOT_REQUIRED_URLS
        )

    def __call__(self, request):
        """Process the request."""
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Redirect to login if URL is one of ``LOGIN_REQUIRED_URLS``."""
        if request.user.is_authenticated:
            return None

        for url in self.login_not_required_urls:
            if url.match(request.path):
                return None

        for url in self.login_required_urls:
            if url.match(request.path):
                return redirect(
                    urls.reverse("accounts:login") + "?next=" + request.path
                )

        return None

"""
Middlewares intercepts requests and process them before they are sent back to the user.
"""
import logging
import re

from django import urls
from django.shortcuts import redirect

from lyprox import settings

logger = logging.getLogger(__name__)


class MaintenanceMiddleware:
    """
    Redirect a visitor to the maintenance page if the ``MAINTENANCE`` is set
    to ``True`` in the `settings`.
    """
    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request):
        path = request.META.get('PATH_INFO', "")

        if settings.MAINTENANCE and not path == urls.reverse("maintenance"):
            response = redirect(urls.reverse("maintenance"))
            return response

        response = self.get_response(request)
        return response


class LoginRequiredMiddleware:
    """
    Redirect a visitor to the login page if the requested URL matches one of the
    ``LOGIN_REQUIRED_URLS`` in the `lyprox.settings`.

    This code is adapted from `stackoverflow`_.

    .. _stackoverflow: https://stackoverflow.com/questions/2164069/best-way-to-make-djangos-login-required-the-default
    """
    def __init__(self, get_response) -> None:
        self.get_response = get_response
        self.login_required_urls = tuple(
            re.compile(url) for url in settings.LOGIN_REQUIRED_URLS
        )
        self.login_not_required_urls = tuple(
            re.compile(url) for url in settings.LOGIN_NOT_REQUIRED_URLS
        )

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Redirect a visitor to the login page if the requested URL matches one of the
        ``LOGIN_REQUIRED_URLS`` in the `lyprox.settings`.
        """
        if request.user.is_authenticated:
            return None

        for url in self.login_not_required_urls:
            if url.match(request.path):
                return None

        for url in self.login_required_urls:
            if url.match(request.path):
                return redirect(urls.reverse("accounts:login") + "?next=" + request.path)

        return None

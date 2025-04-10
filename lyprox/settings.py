"""Main configurations. Explanations of all options can be found in the `Django docs`_.

Generally, the most important settings - but also as few as possible - should be
fetched from environment variables. This is good practice (see `12 Factor App`_) and
especially for security related stuff important. Although LyProX doesn't really have
much security relevant stuff going on.

The settings are written such that errors are thrown when the required environment vars
are not present. This is by design, to ensure the host environment is configured for
the application. It is recommended that you write an ``.env`` file at the root of the
project (DON'T TRACK IT WITH GIT!), from which the environment variables are loaded.
The ``.env`` file should look like this:

.. code-block:: text

    # .env
    DJANGO_ENV=debug
    DJANGO_SECRET_KEY=...

The minimally required environment variables that need to be set are:

- ``DJANGO_ENV`` can be ``"debug"``, ``"maintenance"``, or ``"production"``.
- ``DJANGO_SECRET_KEY`` determines the value of the app's `SECRET_KEY` and must contain
  the secret key for Django's security stuff.
- ``DJANGO_ALLOWED_HOSTS`` needs to contain the allowed host names separated by spaces.
  It will be stored in the `ALLOWED_HOSTS` setting.
- ``DJANGO_LOG_LEVEL`` for Django's `LOG_LEVEL`. This only has an effect in debug mode.
- ``DJANGO_BASE_DIR`` is the directory in which Django is based. Using `BASE_DIR`, this
  is used to determine the location of the database and static files.
- ``GITHUB_TOKEN`` is the token for the GitHub API. This determines the value of the
  corresponding `GITHUB_TOKEN` setting. See this variable's docstring for more details.
  Note that if this is not set, it won't immediately throw an error, but the datasets
  will likely fail to be loaded initially.

.. _Django docs: https://docs.djangoproject.com/en/4.2/ref/settings/
.. _12 Factor App: https://12factor.net/config
"""

import os
from pathlib import Path
from typing import Literal

from django import urls
from django.db import models
from dotenv import load_dotenv
from github import Auth, Github

from ._version import version

if not load_dotenv():
    raise RuntimeError("Failed to load variables from .env file.")

DEBUG = os.environ["DJANGO_ENV"] == "debug"
"""``True``, when in debug mode, meaning ``DJANGO_ENV`` is set to ``"debug"``."""

MAINTENANCE = os.environ["DJANGO_ENV"] == "maintenance"
"""
If ``True``, all requests to are redirected to a maintenance page. ``DJANGO_ENV`` must
be set to ``"maintenance"`` for this to work. Also see `lyprox.views.maintenance`.
"""

PRODUCTION = os.environ["DJANGO_ENV"] == "production"
"""The environment mode.

.. include:: run-local.md
    :start-after: `DJANGO_ENV`:
    :end-before: - `DJANGO_LOG_LEVEL`
    :parser: myst
"""

LOG_LEVEL = os.environ["DJANGO_LOG_LEVEL"] if DEBUG else "WARNING"
"""Minimum level of emitted log messages.

.. include:: run-local.md
    :start-after: `DJANGO_LOG_LEVEL`:
    :end-before: - `DJANGO_SECRET_KEY`
    :parser: myst
"""

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
"""Secret key for cryptography read from the environment variable ``DJANGO_SECRET_KEY``.

.. include:: run-local.md
    :start-after: `DJANGO_SECRET_KEY`:
    :end-before: - `DJANGO_ALLOWED_HOSTS`
    :parser: myst
"""

ALLOWED_HOSTS = os.environ["DJANGO_ALLOWED_HOSTS"].split(" ")
"""From which hosts the application is allowed to be accessed.

.. include:: run-local.md
    :start-after: `DJANGO_ALLOWED_HOSTS`:
    :end-before: - `DJANGO_BASE_DIR`
    :parser: myst
"""

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
"""Authentication token for GitHub API.

.. include:: run-local.md
    :start-after: `GITHUB_TOKEN`:
    :end-before: ## Running the interface
    :parser: myst
"""
GITHUB = Github(auth=Auth.Token(GITHUB_TOKEN))

LNLS = ["I", "Ia", "Ib", "II", "IIa", "IIb", "III", "IV", "V", "Va", "Vb", "VII"]


class TStages(models.IntegerChoices):
    """Tumor stages."""

    # TIS = -2, "TIS"
    # TX  = -1, "TX"
    T0 = 0, "T0"
    T1 = 1, "T1"
    T2 = 2, "T2"
    T3 = 3, "T3"
    T4 = 4, "T4"


CSRF_COOKIE_SECURE = not DEBUG
CRSF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]
SESSION_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 30 if DEBUG else 2_592_000
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(os.environ["DJANGO_BASE_DIR"])
"""Path to the base directory of the project.

.. include:: run-local.md
    :start-after: `DJANGO_BASE_DIR`:
    :end-before: - `GITHUB_TOKEN`
    :parser: myst
"""

LOGIN_URL = urls.reverse_lazy("accounts:login")
"""URL to redirect to when login is required."""

LOGIN_REDIRECT_URL = "/"
"""Redirect to this URL after successful login."""

LOGIN_REQUIRED_URLS = []
"""List of regexes for urls that require login.

Note that this may simply be left empty, since the critical views are protected by
default. But if you want to protect e.g. the entire website, you can add ``"(.*)$"``
to the list.
"""
_login_required_urls_env = os.getenv("DJANGO_LOGIN_REQUIRED_URLS")
if _login_required_urls_env is not None:
    LOGIN_REQUIRED_URLS = _login_required_urls_env.split(" ")

LOGIN_NOT_REQUIRED_URLS = [
    r"/accounts/login/(.*)$",
    r"/accounts/logout/(.*)$",
    r"/admin/(.*)$",
    r"/maintenance/(.*)$",
]
"""List of regexes for urls that are exceptions from the `LOGIN_REQUIRED_URLS`."""

# GitHub repository URL
GITHUB_REPO_OWNER = "rmnldwg"
GITHUB_REPO_NAME = "lyprox"

# versioning
try:
    VERSION = version
except Exception as e:
    VERSION = e

# a frozen version is one we keep for reference to e.g. a publication
IS_FROZEN = False
FROZEN_VERSIONS = [
    {
        "name": "2021 oropharynx data",
        "url": "https://2021-oropharynx.lyprox.org",
    }
]

LogLevelType = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


# Logging
def set_logging(log_level: LogLevelType) -> dict:
    """Return logging settings for specified ``log_level``.

    This is used so that in a subdomain settings file the function
    can be called again to overwrite the logging settings easily.
    """
    return {
        "version": 1,
        "disanle_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)-10s %(name)-40s %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": log_level,
        },
        "loggers": {
            "": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "django": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "lyprox": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }


LOGGING = set_logging(LOG_LEVEL)


# Application definition
INSTALLED_APPS = [
    # my apps
    "lyprox.accounts.apps.AccountsConfig",
    "lyprox.dataexplorer.apps.DataExplorerConfig",
    "lyprox.riskpredictor.apps.RiskConfig",
    # third party apps
    "fontawesomefree",
    "sekizai",
    # django contrib apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "lyprox.middleware.MaintenanceMiddleware",
    "lyprox.middleware.LoginRequiredMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "lyprox.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "lyprox" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "lyprox.context_processors.selected_settings",
                "lyprox.context_processors.navbar_apps",
                "sekizai.context_processors.sekizai",
            ],
            "libraries": {
                "customtags": "lyprox.templatetags.customtags",
            },
        },
    },
]

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Database backup settings
DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
DBBACKUP_STORAGE_OPTIONS = {"location": "/home/rmnldwg/backups/lyprox/"}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"  # noqa: E501
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
AUTH_USER_MODEL = "accounts.User"


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Zurich"
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images) and media (up- & download)
STATIC_ROOT = BASE_DIR / "static"
STATIC_URL = "/static/"

# upload files
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

STATICFILES_DIRS = [BASE_DIR / "lyprox" / "static"]

PUBLICATIONS_PATH = STATIC_ROOT / "publications" / "data.yaml"

JOBLIB_CACHE_DIR = BASE_DIR / ".cache"

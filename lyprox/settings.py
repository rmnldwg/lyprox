"""
Django settings module that defines important configurations. For an explanation of
all the listed values, see the official `Django documentation`_.

Generally, the most important settings - but also as few as possible - should be
fetched from environment variables. The settings are written such that errors are
thrown when the required env vars are not present. This is by design, to ensure the
host environment is configured for the application.

Only these env vars should need to be changed:

- `DJANGO_ENV` can take on the values `"debug"`, `"maintenance"`, or `"production"`.
- `DJANGO_SECRET_KEY` must contain the secret key for Django's security stuff.
- `DJANGO_ALLOWED_HOSTS` needs to contain the allowed host names separated by spaces.
- `DJANGO_LOG_LEVEL` for the log level. This only has an effect in debug mode.
- `DJANGO_BASE_DIR` is the directory in which Django is based.

.. _Django documentation: https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import os
from pathlib import Path

from django import urls
from github import Github

from ._version import version

DEBUG = os.environ["DJANGO_ENV"] == "debug"
"""``True``, when in debug mode, meaning ``DJANGO_ENV`` is set to ``"debug"``."""

MAINTENANCE = os.environ["DJANGO_ENV"] == "maintenance"
"""
If ``True``, all requests to are redirected to a maintenance page. ``DJANGO_ENV`` must
be set to ``"maintenance"`` for this to work. Also see `lyprox.views.maintenance`.
"""

PRODUCTION = os.environ["DJANGO_ENV"] == "production"
"""Set ``DJANGO_ENV`` to ``"production"`` to disable `DEBUG` and `MAINTENANCE` modes."""

LOG_LEVEL = os.environ["DJANGO_LOG_LEVEL"] if DEBUG else "WARNING"
"""
Set the threshold for logging event when in `DEBUG` mode. During ``"maintenance"``
and ``"production"`` this is fixed to ``"WARNING"``. Set via the environment variable
``DJANGO_LOG_LEVEL``.
"""

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
"""
Secret key for cryptographic functions. This is the most sensitive information about
the application. It is set via the environment variable ``DJANGO_SECRET_KEY``.
"""

ALLOWED_HOSTS = os.environ["DJANGO_ALLOWED_HOSTS"].split(" ")
"""
Space-separated list of hostnames for which django will accept requests. Can be set
with the env var ``DJANGO_ALLOWED_HOSTS``.
"""

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
"""
Read-only GitHub access token for fetching information about
`lyprox.riskpredictor.models.InferenceResult`.
"""
GITHUB = Github(login_or_token=GITHUB_TOKEN)


CSRF_COOKIE_SECURE = not DEBUG
CRSF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]
SESSION_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 30 if DEBUG else 2_592_000
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(os.environ["DJANGO_BASE_DIR"])
"""
Setting the base dir manually is necessary, because otherwise everything might be
set up relative to venv's site-packages.
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
        "url" : "https://2021-oropharynx.lyprox.org",
    }
]

# Logging
def set_LOGGING(LOG_LEVEL):
    """Return logging settings in the form of a dictionary as function of the
    log-level. This is used so that in a subdomain settings file the function
    can be called again to overwrite the logging settings easily.
    """
    LOGGING = {
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
            "level": LOG_LEVEL,
        },

        "loggers": {
            "" : {
                "level": LOG_LEVEL,
                "handlers": ["console"],
                "propagate": False,
            },
            "django": {
                "level": LOG_LEVEL,
                "handlers": ["console"],
                "propagate": False,
            },
            "lyprox": {
                "level": LOG_LEVEL,
                "handlers": ["console"],
                "propagate": False,
            },
        }
    }
    return LOGGING

LOGGING = set_LOGGING(LOG_LEVEL)


# Application definition
INSTALLED_APPS = [
    # my apps
    "lyprox.accounts.apps.AccountsConfig",
    "lyprox.patients.apps.PatientsConfig",
    "lyprox.dataexplorer.apps.DataExplorerConfig",
    "lyprox.riskpredictor.apps.RiskConfig",

    # third party apps
    "django_filters",
    "fontawesomefree",
    "phonenumber_field",
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

ROOT_URLCONF = 'lyprox.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "lyprox" / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'lyprox.context_processors.selected_settings',
                'lyprox.context_processors.navbar_apps',
                'sekizai.context_processors.sekizai',
            ],
            'libraries': {
                'customtags': 'lyprox.templatetags.customtags',
            }
        },
    },
]

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Database backup settings
DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
DBBACKUP_STORAGE_OPTIONS = {
    "location": "/home/rmnldwg/backups/lyprox/"
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
AUTH_USER_MODEL = "accounts.User"


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/
LANGUAGE_CODE = 'en-us'
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

STATICFILES_DIRS = [
    BASE_DIR / "lyprox" / "static"
]

PUBLICATIONS_PATH = STATIC_ROOT / "publications" / "data.yaml"

"""Default Django settings for the lyprox web interfaces.

This should not directly be used by e.g. WSGI, but rather another Python file 
named <subdomain>.settings.py should be used for the respective subdomain of 
the interface that overwrites the defaults with appropriate values.
"""
from pathlib import Path
import subprocess
    

# security
DEBUG = True
SECRET_KEY = 'k_&(m5ymps%p=4&qjnwkv-avxb@@ez1tewc8g_eg4k#jx59ukx'
ALLOWED_HOSTS = []
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
FILE_UPLOAD_TEMP_DIR = BASE_DIR / "tmp"
LOGIN_REDIRECT_URL = "/"

# versioning
try:
    VERSION = subprocess.check_output(
        "git describe --tags --always", cwd=BASE_DIR, shell=True
    ).decode("utf-8").strip()
except Exception as e:
    VERSION = e

# the frozen version is the one we keep for reference to the paper
IS_FROZEN = False

# Logging
def set_LOGGING(LOG_LEVEL):
    """Return logging settings in the form of a dictionary as function of the 
    log-level. This is used so that in a subdomain settings file the function 
    can be called again to overwrite the logging settings easily.
    """
    LOGGING = {
        'version': 1,
        'disanle_existing_loggers': False,

        'formatters': {
            'default': {
                'format': "[%(asctime)s] %(levelname)-10s %(name)-40s %(message)s"
            }
        },

        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
            },
            'file': {
                'class': 'logging.FileHandler',
                'filename': BASE_DIR / 'debug.log',
                'formatter': 'default'
            }
        },

        'loggers': {
            'django': {
                'level': LOG_LEVEL,
                'handlers': ['console', 'file']
            },
            'patients': {
                'level': LOG_LEVEL,
                'handlers': ['console', 'file']
            },
            'accounts': {
                'level': LOG_LEVEL,
                'handlers': ['console', 'file']
            },
            'auth_logger': {
                'level': LOG_LEVEL,
                'handlers': ['console', 'file']
            },
            'dashboard': {
                'level': LOG_LEVEL,
                'handlers': ['console', 'file']
            }
        }
    }
    return LOGGING

LOG_LEVEL = "INFO"
LOGGING = set_LOGGING(LOG_LEVEL)


# Application definition
INSTALLED_APPS = [
    # my apps
    "accounts.apps.AccountsConfig",
    "patients.apps.PatientsConfig",
    "dashboard.apps.DashboardConfig",

    # third party apps
    "django_filters",
    # "django_extensions",  # only needed for plotting the model graph
    "phonenumber_field",

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "core" / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.selected_settings'
            ],
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
# TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/
STATICFILES_DIRS = [
    BASE_DIR / "core" / "static"
]

STATIC_ROOT = BASE_DIR / "static"
STATIC_URL = "/static/"

# upload files
MEDIA_ROOT = BASE_DIR / "uploads"
MEDIA_URL = "/media/"

# Download files
DOWNLOADS_ROOT = BASE_DIR / "downloads"
DOWNLOADS_URL = "/downloads/"
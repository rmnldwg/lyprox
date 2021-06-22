from .defaults import *
import os
import warnings

# SECURITY WARNING: keep the secret key used in production secret!
try:
    SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
except KeyError:
    warnings.warn(
        "Secret key not in environment variables. This is fine for "
        "development, but make sure to set it for production!",
        RuntimeWarning
    )
    SECRET_KEY = "k_&(m5ymps%p=4&qjnwkv-avxb@@ez1tewc8g_eg4k#jx59ukx"
    
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
LOG_LEVEL = 'INFO'
LOGGING = set_LOGGING(LOG_LEVEL)

ALLOWED_HOSTS = []

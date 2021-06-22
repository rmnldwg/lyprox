from .defaults import *
import os

# SECURITY WARNING: keep the secret key used in production secret!

try:
    SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
except KeyError as ke:
    raise EnvironmentError(
        "DJANGO_SECRET_KEY not in environment variables. This must be set for "
        "production! Also, make sure it's actually secret!"
    ) from ke
    
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
LOG_LEVEL = 'INFO'
LOGGING = set_LOGGING(LOG_LEVEL)

ALLOWED_HOSTS = []

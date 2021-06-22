from .defaults import *

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
with open(BASE_DIR / "KEY") as f:
    SECRET_KEY = f.read().strip()
    
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
LOG_LEVEL = 'INFO'
LOGGING = set_LOGGING(LOG_LEVEL)

ALLOWED_HOSTS = []
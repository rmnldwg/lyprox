"""The WSGI configuration for the LyProX project. Don't touch it."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lyprox.settings")

application = get_wsgi_application()

"""gunicorn configuration settings."""
import multiprocessing
import os

# Django WSGI application path in pattern MODULE_NAME:VARIABLE_NAME
wsgi_app = "lyprox.wsgi:application"

# The number of worker processes for handling requests
workers = multiprocessing.cpu_count()

# The socket to bind
_port = os.environ["DJANGO_GUNICORN_PORT"]
bind = f"0.0.0.0:{_port}"

# Restart workers when code changes (development only!)
reload = os.environ["DJANGO_ENV"] == "debug"

# The granularity of Error log outputs
loglevel = os.environ["DJANGO_LOG_LEVEL"]

# Write access and error info to stdout/stderr
capture_output = True
accesslog = "-"
errorlog = "-"

# Daemonize the Gunicorn process (detach & enter background)
daemon = False

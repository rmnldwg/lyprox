"""
gunicorn configuration settings.
"""
import os
import multiprocessing


# Django WSGI application path in pattern MODULE_NAME:VARIABLE_NAME
wsgi_app = "core.wsgi:application"

# The number of worker processes for handling requests
workers = multiprocessing.cpu_count()

# The socket to bind
bind = "127.0.0.1:8000"

# Restart workers when code changes (development only!)
reload = os.environ["DJANGO_ENV"] == "debug"

# The granularity of Error log outputs
loglevel = "warning"

# Write access and error info to stdout/stderr
capture_output = True
accesslog = "-"
errorlog = "-"

# PID file so you can easily fetch process ID
pidfile = "/var/run/gunicorn/dev.pid"

# Daemonize the Gunicorn process (detach & enter background)
daemon = False

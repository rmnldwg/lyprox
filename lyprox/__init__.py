"""`LyProX`_ is a `Django`_ app to interactively explore lymphatic progression patterns.

Introduction
============

This is the documentation for the `source code`_ of the `LyProX`_ web app. It is
intended for developers who want to contribute to the project oder use the code for
their own purposes.

We will try to write this documentation as self-contained as possible, because in
our experience, the `Django`_ documentation is not always easy to navigate and learning
by example is often more effective.

The most important modules in this package are:

- the `settings`, where all the configuration of the website is defined. Most
  importantly, it documents all the environment variables that need to be set
  to run the website.
- the `dataexplorer` module, which provides the interactive data exploration tool
  that is the heart of the website.
- the `riskpredictor` module, that allows computing the risk for occult disease,
  given an individual diagnosis as computed by a specified model.

.. contents:: Beyond the documented code, you will also find the following information
    in this documentation:

.. _LyProX: https://lyprox.org
.. _Django: https://djangoproject.com
.. _source code: https://github.com/rmnldwg/lyprox

Maintenance
===========

Beyond understanding and modifying the source code of the app, there is also general
maintenance work to be done. Right now, the web app runs on an `Azure`_ virtual machine.

On this machine, the repository is cloned into the ``/srv/www/lyprox.org`` directory.
A `systemd`_ service provides the `gunicorn`_ server that in turn provides the
interface between the `Django`_ app and the `nginx`_ web server that handles any
incoming requests.

We have chosen `systemd`_ over e.g. docker, because in this simple instance where
we don't need a separate database server or other services, it is easier to set up
and maintain. Note however, that this limits the app to be deployed on virtual machines
that actually have `systemd`_ installed.

Bash Commands
-------------

Here, we give a list of useful commands to see what is going on and perform certain
tasks on the server.

Systemd Commands
^^^^^^^^^^^^^^^^

First, some commands related to the `systemd`_ services:

- ``sudo systemctl status lyprox.org.service``
    Check the status of the `gunicorn`_ server. Ideally, it should show - in addition
    to some general info - the green text ``active (running)``.
- ``sudo systemctl start lyprox.org.service``
    Launch the `gunicorn`_ server. One can also use ``stop`` or ``restart`` to perform
    the corresponding action.
- ``sudo journalctl -u lyprox.org.service -f``
    Shows a continuous stream of the latest log messages emitted by the app. Here,
    one will see the log messages written into the source code of the app.

Similarly, one can inspect the status and logs of the ``nginx.service`` that runs the
interface between the `gunicorn`_ server and the outside world with the corresponding
commands. Simply replace ``lyprox.org`` with ``nginx.service`` in the above commands.

Environment
^^^^^^^^^^^

Next, some commands related to the virtual Python environment and the environment
variables that Django uses for certain settings and secrets:

- ``uv sync``
    We use `uv`_ to manage virtual environments and with this command, one can
    synchronize the virtual environment with the ``requirements.txt`` file. For this to
    work, one needs to be inside the ``/srv/www/lyprox.org`` directory.
- ``set -a; source .env; set +a``
    This command loads all the environment variables from the ``.env`` file into the
    current shell. It is strongly recommended to put the secret key as well as some
    config and passwords into the ``.env`` file and **not** directly in the `settings`.
    Of course, **never** commit the ``.env`` file to source control.

.. _Azure: https://portal.azure.com
.. _systemd: https://systemd.io
.. _gunicorn: https://gunicorn.org
.. _nginx: https://nginx.org
.. _uv: https://docs.astral.sh/uv/

Django Commands
---------------

Built In
^^^^^^^^

Django itself also provides a number of commands that can be run from the command line.
Note that the way we have configured everything, all commands are available under the
``lyprox`` CLI that is installed via the ``uv sync`` command (if the repo is the
current working directory and the virtual environment is activated).

- ``lyprox runserver``
    This starts a Python webserver that is only accessible from the local machine.
    This should **NOT** be used in production, but is useful for development, mostly
    on local machines.
- ``lyprox collectstatic``
    This command collects all static files from the various apps and puts them into
    the directory that is exposed to the internet by the `nginx`_ server. This is
    necessary whenever static files are changed or added.
- ``lyprox migrate``
    This command applies all migrations to the database. In a typical `Django`_ app
    migrations happen sometimes and this command ensures that changes to the database
    model are reflected in the database itself without loosing any data. However, we
    do not really care about loosing data since nothing is stored **only** in the
    `SQLite3`_ database. So, this command is mainly used to initialize the database.
- ``lyprox shell``
    This command starts a Python shell with the `Django`_ environment loaded. This is
    useful for testing code snippets or inspecting the database.

Custom
^^^^^^

All these are provided by `Django`_ itself and are also
`well documented <https://docs.djangoproject.com/en/4.2/ref/django-admin/>`_ in their
docs. Now come a couple of commands that we implemented for ourselves. They are all
about populating the database:

- ``lyprox add_institutions --from-file initial/institutions.json``
    The `add_institutions` command allows creating all the institutions that are
    defined in the ``initial/institutions.json`` file. Institutions must be initialized
    first, because both the users as well as the datasets must belong to an insitution.
- ``lyprox add_users --from-file initial/users.json``
    The `add_users` command allows creating all the users that are defined in the
    ``initial/users.json`` file. Users must be initialized after the institutions,
    because they must belong to an institution. Note that the passwords are not stored
    in the JSON file, but in environment variables (i.e., in the ``.env`` file). The
    name of the environment variable is ``DJANGO_<EMAIL>_PASSWORD``, where ``<EMAIL>``
    is the part of the email address before the ``@`` symbol, with all dots removed.
- ``lyprox add_datasets --from-file initial/datasets.json``
    With the `add_datasets` command, fetching and loading CSV tables of patient records
    from the `lyDATA`_ repo is initiated. The loaded `pandas`_ dataframes are cached
    using `joblib`_ and thus the patient data never reaches the `SQLite3`_ database.
- ``lyprox add_riskmodels --from-file initial/riskmodels.json``
    Lastly, the `add_riskmodels` command loads a model definition from the config files
    that the ``initial/riskmodels.json`` file points to. Then, it fetches the MCMC
    samples for that model and precomputes posterior state distributions for a subset
    of the samples. This is then used in the `riskpredictor` app to compute the
    personalized risk on demand. Again, `joblib`_ is used to cache and speed up the
    results.

.. _lyDATA: https://github.com/rmnldwg/lydata
.. _pandas: https://pandas.pydata.org
.. _joblib: https://joblib.readthedocs.io
.. _SQLite3: https://sqlite.org

Conventions
===========

.. include:: CONTRIBUTING.md
    :start-after: ## Style Conventions
    :end-before: ### Code Style
    :parser: myst

Code Style
----------

.. include:: CONTRIBUTING.md
    :start-after: ### Code Style
    :end-before: ### Docstrings
    :parser: myst

Docstrings
----------

.. include:: CONTRIBUTING.md
    :start-after: ### Docstrings
    :end-before: ### Pre-Commit Hooks and Conventional Commits
    :parser: myst

Pre-Commit Hooks and Conventional Commits
-----------------------------------------

.. include:: CONTRIBUTING.md
    :start-after: ### Pre-Commit Hooks and Conventional Commits
    :end-before: ## Attribution
    :parser: myst

"""

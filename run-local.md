# Run the interface locally

To use this interface on your machine, you can follow these steps below to get it up and running locally on your computer.


## Cloning the repo

Start by cloning this GitHub repository to you machine. In a terminal enter:

```
git clone https://github.com/rmnldwg/lyprox.git
```

Afterwards, `cd` into `lyprox`.


## Set up environment

When working with python, it is always recommended setting up a virtual environment. You can create virtual environments in many ways, but here we are going to use [`venv`](https://docs.python.org/3/library/venv.html), which is pretty simple to use and the recommended tool, according to the Python documentation.

`venv` comes with a Python installation, which I assume you have. So create a blank virtual environment, use this command:

```
python3 -m venv yournewenvironment
```

where you can replace `yournewenvironment` with the name you want to give to your new environment. A common choice is `.venv`, since it's short and the created directory is "hidden" (not really hidden, but it doesn't show up when you type `ls`).

Then, depending on your operating system and used shell, you can activate the environment by typing

| Platform | shell           | command to activate                   |
| :------- | :-------------- | :------------------------------------ |
| POSIX    | bash / zsh      | `$ source <venv>/bin/activate`        |
|          | fish            | `$ source <venv>/bin/activate.fish`   |
|          | csh / tcsh      | `$ source <venv>/bin/activate.csh`    |
|          | PowerShell Core | `$ source <venv>/bin/Activate.ps1`    |
| Windows  | cmd.exe         | `C:\> <venv>\Scripts\activate.bat`    |
|          | cmd.exe         | `PS C:\> <venv>\Scripts\Activate.ps1` |

where `<venv>` should be replaced by the name you have given your virtual environment.

If everything went according to plan, your terminal should now prefix everything with the name of the environment in brackets. E.g. on Ubuntu with bash the terminal now looks like this:

```
(.venv) user@machine:~$
```


## Installing prerequisites

In order to start the interface's server, you need to have [django](https://www.djangoproject.com/) along with several other prerequisites installed. The repository is configured such that pip can install all necessary dependencies as if LyProX were a python package:

```
pip install -U pip setuptools setuptools_scm
pip install .
```


## Configuring environment variables

There are four important settings that the `core/settings.py` file does not define (t conform with the best practices of a [12-factor app]). These settings are instead pulled from environment variables and can be set using the command

```
export ENV_VARIABLE_NAME="variable-value"
```

The four variables that need to be set are:

- `DJANGO_ENV`: can be `"debug"`, `"production"`, or `"maintenance"`. For running the interface locally, it should be set to `"debug"`.
- `DJANGO_SECRET_KEY`: the app-wide secret for authentication and security functions. It can be generated using django's built-in functions. Enter a python REPL by typing `python` into the terminal and then execute these two commands:

    ```python
    >>> from django.core.management.utils import get_random_secret_key
    >>> print(get_random_secret_key()) 
    ```
    
    This will output something like `6-y$g=ek4x!f3kq+=c+f%5@(f1efpdl!(sp&so(bgdli_&_8+n`. Leave the REPL again with `CTRL` + `D`

- `DJANGO_ALLOWED_HOSTS`: space-separated list of hostnames. Set to `"localhost 127.0.0.1"` for local use
- `DJANGO_LOG_LEVEL`: log level. Only has an effect in `"debug"` mode. Is set to `"WARNING"` otherwise


[12-factor app]: https://12factor.net/


## Running the interface

Now you should be ready to execute the following commands:

```
python manage.py makemigrations patients accounts
python manage.py migrate
```

This will prepare django's database. If that worked, it is finally time to launch the server locally:

```
python manage.py runserver
```

If everything goes according to plan, django will output a link to the locally hosted web server. It usually runs at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).


## Populating the database

Since uploading data (also to the local host) requires an authentication, you will want to create a superuser by running

```
python manage.oy createsuperuser
```

Afterwards you can use the defined credentials to log into the admin page at [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) and edit all database entries.

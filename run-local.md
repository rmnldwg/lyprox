# Run the interface locally

If you want to use this interface with your own data locally, or you want to work on the code base of LyProX, you need to be able to run it on your machine. Below, we will detail how that works.

> [!NOTE]
> We work almost exclusively on Linux (Ubuntu, more specifically) and we haven't tested much on other operating systems. So, for best results, try to use Ubuntu as well.

## Prerequisites

You will need a system wide installation of Python. Using that, we recommend installing [pipx], which is a tool to install Python CLIs in their own virtual environments.

After following [their installation instructions](https://pipx.pypa.io/stable/installation/), you should be able to install several tools that are needed to run LyProX or work effectively on its code base (the latter stuff is optional if you only want to run it locally).

1. Install [uv], a new and super fast environment and package manager for Python:

   ```bash
   pipx install uv
   ```

2. (optional) Get [ruff], a versatile and fast linter and code formatter. Simply run

   ```bash
   pipx install ruff
   ```

3. (optional) Install [pre-commit] for checks on the code base just prior to committing changes. This is crucial for collaboration on this project! Again, use [pipx] to insall it:

   ```bash
   pipx install pre-commit
   ```

[uv]: https://docs.astral.sh/uv/
[pipx]: https://pipx.pypa.io/stable/
[ruff]: https://docs.astral.sh/ruff/
[pre-commit]: https://pre-commit.com/

## Cloning the Repo

After all the above requirements are working on your system, continue by cloning this GitHub repository to you machine. Afterwards, make the cloned repo your working directory:

```bash
git clone https://github.com/rmnldwg/lyprox.git
cd lyprox
```

## Virtual Python Environment

When working with Python, it is always recommended setting up a virtual environment. The tool [uv] we installed earlier makes working with virtual environments and installing required Python packages very easy: Simply run the following three commands to (1) create the virtual environment, (2) download and install all necessary Python packages, and (3) activate the environment:

```bash
uv venv
uv sync --all-extras
source .venv/bin/active
```

After some colored output indicating that [uv] has downloaded and installed everything, you should see the text `(lyprox)` prepended to your shell session, like so:

```text
(lyprox) user@machine:~$
```

> [!NOTE]
> If you want to contribute code to the project, now is the time to also install pre-commit to make sure you adhere to the most basic style conventions we use. Please run the following two commands now:
>
> ```bash
> pre-commit install
> pre-commit install --hook-type=commit-msg
> ```

To finally check if LyProX was installed correctly, you can run

```bash
lyprox --help
```

You **should** see a `KeyError: 'DJANGO_ENV'`. We will deal with that error now. If you see `lyprox: command not found`, that would be an issue.

## Configuring environment variables

There are four important settings that the `core/settings.py` file does not define (it conforms with the best practices of a [12-factor app]). These settings are instead pulled from environment variables and can be set using the command

```bash
export ENV_VARIABLE_NAME="variable-value"
```

alternatively, it is possible to place these variables in an `.env` file at the root of the repository that is automatically loaded at server startup. It should have the following format:

```txt
ENV_VARIABLE="variable-value"
```

> [!WARNING]
> **Never** add the `.env` file into your source control system (like git)! It contains secrets that **must not** become public!

The variables that need to be set are:

- `DJANGO_ENV`: Can be `"debug"`, `"production"`, or `"maintenance"`. For running the interface locally, it should be set to `"debug"`.
- `DJANGO_LOG_LEVEL`: The log level only has an effect in `"debug"` mode. Is set to `"WARNING"` otherwise.
- `DJANGO_SECRET_KEY`: This is the app-wide secret for authentication and security functions. It can be generated using django's built-in functions. Enter a python REPL by typing `python` into the terminal and then execute these two commands:

  ```python
  >>> from django.core.management.utils import get_random_secret_key
  >>> print(get_random_secret_key())
  ```

  This will output something like `6-y$g=ek4x!f3kq+=c+f%5@(f1efpdl!(sp&so(bgdli_&_8+n`. Note that this is *the* most sensitive variable for the security of the web app!

- `DJANGO_ALLOWED_HOSTS`: This is space-separated list of hostnames from which access is allowed. Set to `"localhost 127.0.0.1"` for local use. For deployment this should be changed to the domain name you are using.
- `DJANGO_BASE_DIR`: The base directory of the server is ypically the root of the repository. From this directory, the web app infers the location of a couple of directories and paths it needs e.g. for loading and storing static files and media stuff. If this isn't set, one might end up with a situation where Django tries to set up everything relative to the ``site-packages`` folder inside the ``.venv``.
- `GITHUB_TOKEN`: A personal secret for accessing GitHub's official API. This is used to access the [lyDATA](https://github.com/rmnldwg/lydata) repo and fetch the datasets. Refer to the [GitHub documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) on how to create such a token.
- `DJANGO_ADMIN_EMAIL`: The email address of the web app's administrator. This will be displayed on the website and it will also be sent to crossref when the [habanero](https://habanero.readthedocs.io/en/latest/index.html) module makes a request to fetch metadata for the list of publications on the landing page.

[12-factor app]: https://12factor.net/

## Running the interface

Now you should be ready to execute the following commands:

```bash
lyprox migrate
lyprox collectstatic
```

This will prepare django's database. If that worked, you should [`add_institutions`](https://lycosystem.github.io/lyprox/lyprox.accounts.management.commands.add_institutions.html) and [`add_users`](https://lycosystem.github.io/lyprox/lyprox.accounts.management.commands.add_users.html) to the database. Check the linked documentation to see how these two commands work.

```bash
lyprox add_institutions ...
lyprox add_users ...
```

If you want to also [`add_datasets`](https://lycosystem.github.io/lyprox/lyprox.dataexplorer.management.commands.add_datasets.html), you can do so in a similar fashion. Make sure to check the docs.

If everything up to this point went according to plan, you can now launch the interface:

```bash
lyprox runserver
```

And it should give you a response with a link that you can open in your browser and play with a live version of LyProX! 🥳

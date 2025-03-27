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

The variables that need to be set are:

- `DJANGO_ENV`: can be `"debug"`, `"production"`, or `"maintenance"`. For running the interface locally, it should be set to `"debug"`.
- `DJANGO_SECRET_KEY`: the app-wide secret for authentication and security functions. It can be generated using django's built-in functions. Enter a python REPL by typing `python` into the terminal and then execute these two commands:

    ```python
    >>> from django.core.management.utils import get_random_secret_key
    >>> print(get_random_secret_key())
    ```

    This will output something like `6-y$g=ek4x!f3kq+=c+f%5@(f1efpdl!(sp&so(bgdli_&_8+n`. Leave the REPL again with `CTRL` + `D`

- `DJANGO_ALLOWED_HOSTS`: space-separated list of hostnames. Set to `"localhost 127.0.0.1"` for local use
- `DJANGO_LOG_LEVEL`: log level. Only has an effect in `"debug"` mode. Is set to `"WARNING"` otherwise
- `DJANGO_BASE_PATH`: The base directory of the server. Typically the root of the repository.
- `GITHUB_TOKEN`: A personal GitHub token for the API. This is used to access the [lyDATA] repo and fetch the datasets. Refer to the [GitHub documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) on how to create such a token.

[12-factor app]: https://12factor.net/
[lyDATA]: https://github.com/rmnldwg/lydata

## Running the interface

Now you should be ready to execute the following commands:

```bash
lyprox migrate
lyprox collectstatic
```

This will prepare django's database. If that worked, you should [`add_institutions`](https://rmnldwg.github.io/lyprox/lyprox.accounts.management.commands.add_institutions.html) and [`add_users`](https://rmnldwg.github.io/lyprox/lyprox.accounts.management.commands.add_users.html) to the database. Check the linked documentation to see how these two commands work.

```bash
lyprox add_institutions ...
lyprox add_users ...
```

If you want to also [`add_datasets`](https://rmnldwg.github.io/lyprox/lyprox.dataexplorer.management.commands.add_datasets.html), you can do so in a similar fashion. Make sure to check the docs.

If everything up to this point went according to plan, you can now launch the interface:

```bash
lyprox runserver
```

And it should give you a response with a link that you can open in your browser and play with a live version of LyProX! 🥳

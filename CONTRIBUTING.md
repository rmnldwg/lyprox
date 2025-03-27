<!-- omit in toc -->
# Contributing to LyProX

First off, thanks for taking the time to contribute! ❤️

All types of contributions are encouraged and valued. See the [Table of Contents](#table-of-contents) for different ways to help and details about how this project handles them. Please make sure to read the relevant section before making your contribution. It will make it a lot easier for us maintainers and smooth out the experience for all involved. The community looks forward to your contributions. 🎉

And if you like the project, but just don't have time to contribute, that's fine. There are other easy ways to support the project and show your appreciation, which we would also be very happy about:

- Star the project
- Tweet about it
- Refer this project in your project's readme
- Mention the project at local meetups and tell your friends/colleagues

<!-- omit in toc -->
## Table of Contents

- [I Have a Question](#i-have-a-question)
- [I Want To Contribute](#i-want-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Your First Code Contribution](#your-first-code-contribution)
- [Conventions](#conventions)
  - [Code Style](#code-style)
  - [Docstrings](#docstrings)
  - [Pre-Commit Hooks and Conventional Commits](#pre-commit-hooks-and-conventional-commits)

## I Have a Question

> If you want to ask a question, we assume that you have read the available [Documentation](https://rmnldwg.github.io/lyprox/).

Before you ask a question, it is best to search for existing [Issues](https://github.com/rmnldwg/lyprox/issues) that might help you. In case you have found a suitable issue and still need clarification, you can write your question in this issue. It is also advisable to search the internet for answers first.

If you then still feel the need to ask a question and need clarification, we recommend the following:

- Open an [Issue](https://github.com/rmnldwg/lyprox/issues/new).
- Provide as much context as you can about what you're running into.
- Provide project and platform versions (nodejs, npm, etc), depending on what seems relevant.

We will then take care of the issue as soon as possible.

## I Want To Contribute

> ### Legal Notice <!-- omit in toc -->
>
> When contributing to this project, you must agree that you have authored 100% of the content, that you have the necessary rights to the content and that the content you contribute may be provided under the project licence.

### Reporting Bugs

<!-- omit in toc -->
#### How Do I Submit a Good Bug Report?

We use GitHub issues to track bugs and errors. If you run into an issue with the project:

- Open an [Issue](https://github.com/rmnldwg/lyprox/issues/new). (Since we can't be sure at this point whether it is a bug or not, we ask you not to talk about a bug yet and not to label the issue.)
- Explain the behavior you would expect and the actual behavior.
- Please provide as much context as possible and describe the *reproduction steps* that someone else can follow to recreate the issue on their own. This usually includes your code. For good bug reports you should isolate the problem and create a reduced test case.
- Provide the information you collected in the previous section.

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for LyProX, **including completely new features and minor improvements to existing functionality**. Following these guidelines will help maintainers and the community to understand your suggestion and find related suggestions.

<!-- omit in toc -->
#### How Do I Submit a Good Enhancement Suggestion?

Enhancement suggestions are tracked as [GitHub issues](https://github.com/rmnldwg/lyprox/issues).

- Use a **clear and descriptive title** for the issue to identify the suggestion.
- Provide a **step-by-step description of the suggested enhancement** in as many details as possible.
- **Describe the current behavior** and **explain which behavior you expected to see instead** and why. At this point you can also tell which alternatives do not work for you.
- You may want to **include screenshots or screen recordings** which help you demonstrate the steps or point out the part which the suggestion is related to.
- **Explain why this enhancement would be useful** to most LyProX users. You may also want to point out the other projects that solved it better and which could serve as inspiration.

### Your First Code Contribution

The first thing if you want to contribute code to the project is to get it running on your machine. To achieve that, read through the [respective instructions](./run-local.md) that we have put together.

Also, make sure you do understand how to use [git] and [GitHub] for collaborative development. Here is an [excellent guide](https://www.dataschool.io/how-to-contribute-on-github/) on forking a repository and merging back edits.

[git]: https://git-scm.com
[GitHub]: https://github.com

## Conventions

To keep the code and documentation clean and readable, we follow a few conventions. Any contributions should adhere to these style conventions.

### Code Style

We use [ruff] to format the code. The selected and ignored rules are specified in the `pyproject.toml` file at the root of the repository.

Also, we are big fans of [type hints](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html) in function arguments and class attributes and use them wherever possible. While not enforced, as there may be cases where type hints are not feasible or useful, we generally strive to use them extensively.

[ruff]: https://docs.astral.sh/ruff/

### Docstrings

Docstrings should follow the format below. Note that we don't like the styles where the docstring lists all function arguments and their types *again*. We think this is redundant as long as

- the argument names are meaningful
- all arguments are type hinted
- the use and effect of each argument is described in the body of the docstring

Therefore, we write docstring that create documentations that look similar to how the [main Python docs](https://docs.python.org/3.10/library/functions.html#getattr) are structured (note the linked example of `getattr()`).

```python
def my_function(arg1: int, arg2: str) -> float:
    """Briefly describe what the function does.

    Then go on and describe it in detail. Make sure to mention what `arg1` does
    and also what the effect of `arg2` is.

    We are not huge fans of, e.g., Google-style docstrings where every parameter
    is separately listed and described. Instead, use descriptive names for the
    arguments and describe them in the text. The main Python documentation
    follows a similar style.
    """
    print(arg2)
    return 3.14 + arg1
```

When using docstrings as above, the documentation can be auto-generated from the code using [pydoctor]. Its output is simple, clean, and comprehensive. It lists all modules, classes, and functions in the same hierarchy as they appear in the codebase. If the docstrings are well-written, they can effectively guide the reader through the codebase. Cross-references can be added using single backticks, e.g., `` `my_symbol` `` will search the entire codebase (and even other linked docs) for this symbol and add a link to it if found.

[pydoctor]: https://pydoctor.readthedocs.io/en/latest/

### Pre-Commit Hooks and Conventional Commits

We use [pre-commit] to run [ruff] and other checks before every commit. This ensures that the code adheres to some basic standards and that all commit messages are so-called [conventional commits]. To enable this, you need to install [pre-commit] (e.g., by running `uv add pre-commit` or, better yet, by installing it via [pipx]) and then install the following two hooks:

```bash
pre-commit install
pre-commit install --hook-type=commit-msg
```

[pre-commit]: https://pre-commit.com/
[pipx]: https://pipx.pypa.io/
[conventional commits]: https://www.conventionalcommits.org/en/v1.0.0/

<!-- omit in toc -->
## Attribution

This guide was partially created by the [contributing.md](https://contributing.md/generator) generator!

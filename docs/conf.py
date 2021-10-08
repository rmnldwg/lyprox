# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys
sys.path.insert(0, os.path.abspath('..'))
import django
from django.conf import settings
from core.settings import INSTALLED_APPS, SECRET_KEY, VERSION


settings.configure(
    INSTALLED_APPS = INSTALLED_APPS,
    SECRET_KEY = SECRET_KEY
)

django.setup()


# -- Project information -----------------------------------------------------

project = 'LyProX'
copyright = '2021, Roman Ludwig'
author = 'Roman Ludwig'

# The full version, including alpha/beta/rc tags
release = VERSION


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx_markdown_builder"
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

html_title = "Documentation for Django-based interface"

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

colors = {
    "primary": "#005EA8",
    "primary-light": "#EBF6FF",
    "info": "#BDCFD6",
    "info-light": "#F2F6F7",
    "success": "#00AFA5",
    "success-light": "#EBFFFE",
    "warning": "#F17900",
    "warning-light": "#FFEEDE",
    "danger": "#AE0060",
    "danger-light": "#FFEBF6"
}

html_permalinks_icon = '#'
html_theme = "furo"
html_favicon = "../core/static/favicon.ico"
html_logo = "../core/static/logo.svg"
html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": colors["primary"],
        "color-brand-content": colors["primary"],
        "color-problematic": colors["danger"],
        "color-foreground-secondary": colors["primary"],
        "color-foreground-muted": colors["primary"],
        "color-background-secondary": colors["primary-light"],
        "color-background-hover": "#DEF0FF",
        
        # Admonitions / Notification
        "color-admonition-title--attention": colors["danger"],
        "color-admonition-title-background--attention": colors["danger-light"],
        "color-admonition-title--danger": colors["danger"],
        "color-admonition-title-background--danger": colors["danger-light"],
        "color-admonition-title--error": colors["danger"],
        "color-admonition-title-background--error": colors["danger-light"],
        "color-admonition-title--hint": colors["success"],
        "color-admonition-title-background--hint": colors["success-light"],
        "color-admonition-title--tip": colors["success"],
        "color-admonition-title-background--tip": colors["success-light"],
        "color-admonition-title--important": colors["warning"],
        "color-admonition-title-background--important": colors["warning-light"],
        "color-admonition-title--warning": colors["warning"],
        "color-admonition-title-background--warning": colors["warning-light"],
        "color-admonition-title--caution": colors["warning"],
        "color-admonition-title-background--caution": colors["warning-light"],
        "color-admonition-title--note": colors["primary"],
        "color-admonition-title-background--note": colors["primary-light"],
        "color-admonition-title--seealso": colors["warning"],
        "color-admonition-title-background--seealso": colors["warning-light"],
        "color-admonition-title--admonition-todo": colors["info"],
        "color-admonition-title-background--admonition-todo": colors["info-light"],
        
        "font-stack": "Segoe UI, sans-serif",
        "font-stack--monospace": "Cascadia Code, monospace",
    }
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_css_files = ["css/custom.css"]
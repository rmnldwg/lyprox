"""Custom tags and filters for Django's HTML templating.

Surprisingly, Django's templating does not provide some basic functionality I expected
to be there. So, I had to write some custom tags (like the sum of a list) and filters
specific to LyProX's needs.
"""

import ast
import json
import logging
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, TypeVar
from urllib.parse import urlparse

import markdown as md
import yaml
from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from mdx_math import MathExtension

from lyprox.settings import MEDIA_URL

register = template.Library()
logger = logging.getLogger(__name__)


def safe_eval(expr: str) -> Any:
    """Safely evaluate an expression."""
    if expr not in ["True", "False", "None"]:
        raise ValueError(f"Invalid expression: {expr}")

    return ast.literal_eval(expr)


class MyMathExtension(MathExtension):
    """Custom math extension for markdown."""

    def __init__(self, *args, **kwargs):
        """Initialize the extension."""
        super().__init__(*args, **kwargs)
        self.config.update(
            {
                "enable_dollar_delimiter": [True, "Enable single-dollar delimiter"],
            }
        )


T = TypeVar("T")


@register.filter(name="index")
def index(seq: Sequence[T], i: str) -> T:
    """Get the ``i``-th element of ``seq``.

    Allows one to use ``{{ seq|index:'i' }}`` in Django templates.
    """
    i = int(f"{i}".lower())
    return seq[i]


@register.filter(name="barplot_css")
def barplot_css(value_counts: dict[Any, int], argstr: str) -> float:
    """Return the relative width to be sent to the CSS for the dashboard's bar plot.

    Use it like this in the HTML templates:
    ``{{ value_counts|barplot_css:'<key>,<width>' }}``, where the key and the total
    width are separated by a comma. The key is the key of the value in the
    ``value_counts`` dict and the width is the total width of the bar plot.
    """
    keystr, widthstr = argstr.split(",")
    key = safe_eval(keystr)
    width = float(widthstr)
    total = sum(list(value_counts.values()))
    return width * value_counts[key] / total


N = TypeVar("N", int, float)


@register.filter(name="sum")
def sum_(iterable: Iterable[N]) -> N:
    """Implement the sum im Django templates.

    Use it like this: ``{{ mylist|sum }}`` or ``{{ mydict.values|sum }}``.
    """
    return sum(iterable)


@register.filter(name="multiply")
def multiply(value: N, factor: N) -> N:
    """Multiply ``value`` by ``factor``."""
    return value * factor


@register.filter(name="capitalize_subsite")
def capitalize_subsite(subsite: str) -> str:
    """Capitalize the subsite name."""
    result = subsite.replace("Subsite", "")
    result = result.lstrip().rstrip()
    result = result.split(" ")
    result = " ".join([word.capitalize() for word in result])
    return result.replace("Of", "of")


@register.filter(name="get_logo")
def get_logo(dataset: str) -> str:
    """Get the logo of the institution providing a dataset."""
    abbr = dataset.split("-")[1].lower()
    return f"{MEDIA_URL}logos/{abbr}.png"


@register.filter(name="get_subsite")
def get_subsite(dataset: str) -> str:
    """Get the subsite name from the dataset name."""
    result = " ".join([word.capitalize() for word in dataset.split(" ")[-1].split("-")])
    if result == "Hypopharynx Larynx":
        result = "Hypo. & Larynx"
    return result


def custom_markdown(text: str) -> str:
    """Render custom markdown with footnotes and tables."""
    return md.markdown(text, extensions=["footnotes", "tables", MyMathExtension()])


@register.simple_tag(name="include_md", takes_context=True)
def include_md(context: template.RequestContext, template_name: str) -> str:
    """Include a markdown file in the template.

    The markdown file may also include Django template tags, just as the HTML. This tag
    is used like this: ``{% include_md "path/to/file.md" %}``.
    """
    # 'context' here isn't a dictionary, but an instance of RequestContext
    context_dict = {k: v for subdict in context.dicts for k, v in subdict.items()}
    # parse the template and fill the tags with context variables
    template = render_to_string(template_name, context=context_dict)
    return mark_safe(custom_markdown(template))  # noqa: S308


@register.simple_tag(name="render_md")
def render_md(raw: str):
    """Render raw markdown text."""
    return mark_safe(custom_markdown(raw))  # noqa: S308


@register.simple_tag(name="render_json")
def render_json(raw: str) -> str:
    """Format and render raw JSON text."""
    return json.dumps(raw, indent=4)


@register.simple_tag(name="render_yaml")
def render_yaml(raw: str) -> str:
    """Format and render raw YAML text."""
    return yaml.safe_dump(raw, sort_keys=False, default_flow_style=False)


@register.filter(name="concat")
def concat(this: str, other: str) -> str:
    """Concatenate ``this`` & ``other``."""
    return str(this) + str(other)


KT = TypeVar("KT")
VT = TypeVar("VT")


@register.filter(name="get")
def get(mapping: Mapping[KT, VT], key: KT) -> VT | None:
    """Get an item from dict-like ``mapping`` using ``key``."""
    try:
        return mapping[key]
    except KeyError:
        return None


@register.filter(name="get_percent")
def get_percent(value_counts: dict[Any, int], key: Any) -> str:
    """Get the percentage ``value_counts[key]`` in the total of ``value_counts``.

    Use it like this in the HTML templates: ``{{ value_counts|get_percent:key }}``.
    """
    total = sum(list(value_counts.values()))
    return " - " if total == 0 else f"{100 * value_counts[key] / total:.0f}"


@register.filter(name="getattr")
def getattr_(instance, attr) -> Any:
    """Get an attribute from ``instance`` using ``attr``."""
    return getattr(instance, attr, None)


@register.filter(name="remove_host")
def remove_host(url: str) -> str:
    """Remove host from ``url``. So, ``https://foo.com/bar/baz`` becomes ``bar/baz``."""
    return urlparse(url).path[1:]


@register.simple_tag(name="to_list")
def to_list(*args) -> list:
    """Convert arguments to a list.

    This is useful if you want to iterate over a list of items in a Django template
    and you don't want to provide that list to the context, but 'harcoded' in the
    template. Use it like this: ``{% to_list 1 2 3 4 as mylist %}`` and then afterwards
    you can iterate over ``mylist``.
    """
    return list(args)

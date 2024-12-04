import ast
import json
import logging
from typing import Any
from urllib.parse import urlparse

import markdown as md
import yaml
from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from mdx_math import MathExtension

register = template.Library()
logger = logging.getLogger(__name__)


def safe_eval(expr: str) -> Any:
    """Safely evaluate an expression."""
    if expr not in ["True", "False", "None"]:
        raise ValueError(f"Invalid expression: {expr}")

    return ast.literal_eval(expr)


class MyMathExtension(MathExtension):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config.update({
            "enable_dollar_delimiter": [True, "Enable single-dollar delimiter"],
        })


@register.filter(name="index")
def index(indexable, i):
    return indexable[int(f"{i}".lower())]

@register.filter(name="bar")
def bar(value_counts: dict[Any, int], argstr: str):
    keystr, widthstr = argstr.split(',')
    key = safe_eval(keystr)
    width = float(widthstr)
    total = sum(list(value_counts.values()))
    return width * value_counts[key] / total

@register.filter(name="sum")
def mysum(value_counts: dict[Any, int]) -> int:
    return sum(counts for counts in value_counts.values())

@register.filter(name="multiply")
def myprod(num, fac):
    return num * fac

@register.filter(name="percent")
def percent(value_counts: dict[Any, int], key: Any) -> str:
    total = sum(count for count in value_counts.values())
    return " - " if total == 0 else f"{100 * value_counts[key] / total:.0f}"

def custom_markdown(text):
    return md.markdown(text, extensions=["footnotes", "tables", MyMathExtension()])

@register.simple_tag(name="include_md", takes_context=True)
def include_md(context, template_name):
    # 'context' here isn't a dictionary, but an instance of RequestContext
    context_dict = {k: v for subdict in context.dicts for k,v in subdict.items()}
    # parse the template and fill the tags with context variables
    template = render_to_string(template_name, context=context_dict)

    html_string = custom_markdown(template)
    return mark_safe(html_string)

@register.simple_tag(name="render_md")
def render_md(raw):
    return mark_safe(custom_markdown(raw))

@register.simple_tag(name="render_json")
def render_json(raw):
    json_string = json.dumps(raw, indent=4)
    return json_string

@register.simple_tag(name="render_yaml")
def render_yaml(raw):
    yaml_string = yaml.safe_dump(raw, sort_keys=False, default_flow_style=False)
    return yaml_string

@register.filter(name="addstr")
def addstr(this, other):
    """Concatenate `this` & `other`."""
    return str(this) + str(other)

@register.filter(name="get")
def get(object, key):
    """Get an item from dict-like `object` using `key`."""
    try:
        return object[key]
    except KeyError:
        return None

@register.filter(name="getattr")
def getattribute(object, key):
    """Get an item from dict-like `object` using `key`."""
    return getattr(object, key, None)

@register.filter(name="remove_host")
def remove_host(url):
    """Remove the host from `url`. So, `https://foo.com/bar/baz` becomes `bar/baz`."""
    return urlparse(url).path[1:]

@register.simple_tag(name="to_list")
def to_list(*args) -> list:
    """Convert arguments to a list."""
    return list(args)

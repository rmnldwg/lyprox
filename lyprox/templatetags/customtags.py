import json
import logging
from urllib.parse import urlparse

import markdown as md
import yaml
from django import template
from django.template.loader import render_to_string
from django.utils.html import format_html

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter(name="index")
def index(indexable, i):
    return indexable[int(f"{i}".lower())]

@register.filter(name="bar")
def bar(indexable, argstr):
    istr, widthstr = argstr.split(',')
    i = int(istr)
    width = float(widthstr)
    total = sum(indexable)
    return width * indexable[i] / total

@register.filter(name="sum")
def mysum(indexable):
    return sum(indexable)

@register.filter(name="multiply")
def myprod(num, fac):
    return num * fac

@register.filter(name="percent")
def percent(indexable, i):
    i = int(f"{i}".lower())
    total = sum(indexable)
    if total == 0:
        return " - "
    else:
        return f"{100 * indexable[i] / total:.0f}"

def custom_markdown(text):
    return md.markdown(text, extensions=["footnotes", "tables"])

@register.simple_tag(name="include_md", takes_context=True)
def include_md(context, template_name):
    # 'context' here isn't a dictionary, but an instance of RequestContext
    context_dict = {k: v for subdict in context.dicts for k,v in subdict.items()}
    # parse the template and fill the tags with context variables
    template = render_to_string(template_name, context=context_dict)

    html_string = custom_markdown(template)
    return format_html(html_string)

@register.simple_tag(name="render_md")
def render_md(raw):
    return format_html(custom_markdown(raw))

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

@register.filter(name="remove_host")
def remove_host(url):
    """Remove the host from `url`. So, `https://foo.com/bar/baz` becomes `bar/baz`."""
    return urlparse(url).path[1:]

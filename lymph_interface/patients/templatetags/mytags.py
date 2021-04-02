from django import template
register = template.Library()

@register.filter(name="index")
def index(indexable, i):
    return indexable[i]
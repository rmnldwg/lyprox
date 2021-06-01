from django import template
register = template.Library()

@register.filter(name="index")
def index(indexable, i):
    return indexable[i]

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

@register.filter(name="percent")
def percent(indexable, i):
    return f"{100 * indexable[i] / sum(indexable):.1f}"
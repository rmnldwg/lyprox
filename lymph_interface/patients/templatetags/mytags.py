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
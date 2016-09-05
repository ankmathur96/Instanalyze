from django import template
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape

register = template.Library()

@register.filter(name='plustwo')
def plustwo(value):
    return int(value) + 2

@register.filter(name='slice')
def slice(value, arg):
	return value[int(arg):]
import json
import re

from django import template

register = template.Library()

@register.filter(name='fixproxyurl')
def fixproxyurl(value):
    # Some PopIt versions have a double-slash accidentally included:
    return re.sub(r'image-proxy//', 'image-proxy/', value)

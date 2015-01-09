import json
import re

from django import template
from django.conf import settings

register = template.Library()

@register.filter(name='fixproxyurl')
def fixproxyurl(value):
    # Some PopIt versions have a double-slash accidentally included:
    result = re.sub(r'image-proxy//', 'image-proxy/', value)
    if settings.FORCE_HTTPS_IMAGES:
        # Then nake sure that we're using an HTTPS URL:
        result = re.sub(r'^http://', 'https://', result)
    return result

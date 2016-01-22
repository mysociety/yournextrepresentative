# -*- coding: utf-8 -*-

from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

register = template.Library()


@register.filter
def extra_field_value(extra_field):
    if extra_field['value'] == '':
        return ''

    if extra_field['type'] == 'url':
        url = conditional_escape(extra_field['value'])
        output = \
            u'<a href="{0}" rel="nofollow">{0}</a>'.format(url)
        output = mark_safe(output)
    elif extra_field['type'] == 'yesno':
        output = {
            'yes': _(u'Yes'),
            'no': _(u'No'),
        }.get(extra_field['value'], _(u"Don’t Know"))
    else:
        output = extra_field['value']
    return output

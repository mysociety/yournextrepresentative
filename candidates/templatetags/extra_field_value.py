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
        if extra_field['value'] == 'yes':
            output = _(u'Yes')
        elif extra_field['value'] == 'no':
            output = _(u'No')
        else:
            output = _(u"Don't know")
    else:
        output = extra_field['value']
    return output

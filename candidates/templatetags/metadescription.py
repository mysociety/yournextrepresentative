import re

from django import template
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.utils.translation import ugettext as _

register = template.Library()

@register.simple_tag
def metadescription(person, last_cons, today):
    if person.last_party:
        last_party_name = person.last_party['name'].strip()
        last_party_name = re.sub('^The ', 'the ', last_party_name)
        args = {
            'election': last_cons[0],
            'name': person.name,
            'party': last_party_name,
            'post': last_cons[1]['name'],
        }
        if is_post_election(last_cons[0], today):
            if last_party_name == "Independent":
                output = _("%(name)s stood as an independent candidate in %(post)s in %(election)s") % args
            else:
                output = _("%(name)s stood for %(party)s in %(post)s in %(election)s") % args
        else:
            if last_party_name == "Independent":
                output = _("%(name)s is standing as an independent candidate in %(post)s in %(election)s") % args
            else:
                output = _("%(name)s is standing for %(party)s in %(post)s in %(election)s") % args
    else:
        output = person.name

    output += " - " + _("find out more on YourNextMP")
    return output

def is_post_election(election, today):
    return today > settings.ELECTIONS[election]['election_date']

@register.filter
def static_image_path(image_name, request):
    abs_path = static(image_name)
    return request.build_absolute_uri(abs_path)

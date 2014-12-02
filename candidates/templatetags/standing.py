from slugify import slugify

from django import template
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def constituency_in_year(person, year):
    if year not in person['standing_in']:
        if year == "2010":
            result = u'<span class="constituency-not-standing">Did not stand in 2010</span>'
        else:
            result = u'<span class="constituency-value-unknown">No information yet</span>'
    elif not person['standing_in'][year]:
        if year == "2010":
            result = u'<span class="constituency-value-not-standing">Did not stand in 2010</span>'
        else:
            result = u'<span class="constituency-value-not-standing">Not standing in {0}</span>'
        result = result.format(year)
    else:
        link = u'<a href="{cons_url}">{cons_name}</a>'.format(
            cons_url=reverse(
                'constituency',
                kwargs={
                    'mapit_area_id': person['standing_in'][year]['post_id'],
                    'ignored_slug': slugify(person['standing_in'][year]['name']),
                }
            ),
            cons_name=person['standing_in'][year]['name']
        )
        result = u'<span class="constituency-value-standing-link">{0}</span>'.format(
            link
        )
        result += u' <span class="party">{0}</span>'.format(
            person['party_memberships'][year]['name']
        )
    return mark_safe(result)

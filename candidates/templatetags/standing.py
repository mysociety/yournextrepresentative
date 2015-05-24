from slugify import slugify

from django import template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def constituency_in_year(person, election):
    standing_in = person.standing_in
    election_data = settings.ELECTIONS[election]
    if election not in standing_in:
        if election_data.get('current'):
            result = u'<span class="constituency-value-unknown">No information yet</span>'
        else:
            result = u'<span class="constituency-not-standing">Did not stand</span>'
    elif not standing_in[election]:
        if election_data.get('current'):
            result = u'<span class="constituency-value-not-standing">Not standing</span>'
        else:
            result = u'<span class="constituency-value-not-standing">Did not stand</span>'
    else:
        link = u'<a href="{cons_url}">{cons_name}</a>'.format(
            cons_url=reverse(
                'constituency',
                kwargs={
                    'election': election,
                    'mapit_area_id': standing_in[election]['post_id'],
                    'ignored_slug': slugify(standing_in[election]['name']),
                }
            ),
            cons_name=standing_in[election]['name']
        )
        result = u'<span class="constituency-value-standing-link">{0}</span>'.format(
            link
        )
        result += u' <span class="party">{0}</span>'.format(
            person.party_memberships[election]['name']
        )
    return mark_safe(result)

@register.filter
def election_decision_known(person, election):
    return person.get_elected(election) is not None

@register.filter
def was_elected(person, election):
    return bool(person.get_elected(election))

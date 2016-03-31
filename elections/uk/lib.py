from __future__ import unicode_literals

import re

from popolo.models import Identifier

from candidates.models import MembershipExtra
from candidates.mapit import get_areas_from_coords

from .mapit import get_areas_from_postcode


def shorten_post_label(post_label):
    result = re.sub(r'^Member of Parliament for ', '', post_label)
    result = re.sub(r'^Member of the Scottish Parliament for ', '', result)
    result = re.sub(r'^Assembly Member for ', '', result)
    result = re.sub(r'^Member of the Legislative Assembly for ', '', result)
    return result


EXTRA_CSV_ROW_FIELDS = [
    'gss_code',
    'parlparse_id',
    'theyworkforyou_url',
    'party_ec_id',
]

def get_extra_csv_values(person, election):
    theyworkforyou_url = ''
    parlparse_id = ''
    try:
        i = person.identifiers.get(scheme='uk.org.publicwhip')
        parlparse_id = i.identifier
        m = re.search(r'^uk.org.publicwhip/person/(\d+)$', parlparse_id)
        if not m:
            message = "Malformed parlparse ID found {0}"
            raise Exception(message.format(parlparse_id))
        theyworkforyou_url = 'http://www.theyworkforyou.com/mp/{0}'.format(
            m.group(1)
        )
    except Identifier.DoesNotExist:
        pass
    candidacy = MembershipExtra.objects \
        .select_related('base', 'base__post', 'base__post__area') \
        .get(
            election=election,
            base__person=person,
            base__role=election.candidate_membership_role,
        )
    post = candidacy.base.post
    party = candidacy.base.on_behalf_of
    try:
        party_ec_id = party.identifiers.get(scheme='electoral-commission').identifier
    except Identifier.DoesNotExist:
        party_ec_id = ''
    try:
        gss_code = post.area.other_identifiers.get(scheme='gss')
    except Identifier.DoesNotExist:
        gss_code = None
    return {
        'gss_code': gss_code,
        'parlparse_id': parlparse_id,
        'theyworkforyou_url': theyworkforyou_url,
        'party_ec_id': party_ec_id
    }


def fetch_area_ids(**kwargs):
    if kwargs['postcode']:
        areas = get_areas_from_postcode(kwargs['postcode'])

    if kwargs['coords']:
        areas = get_areas_from_coords(kwargs['coords'])

    return areas

def is_valid_postcode(postcode):
    outcode_pattern = '[A-PR-UWYZ]([0-9]{1,2}|([A-HIK-Y][0-9](|[0-9]|[ABEHMNPRVWXY]))|[0-9][A-HJKSTUW])'
    incode_pattern = '[0-9][ABD-HJLNP-UW-Z]{2}'
    postcode_regex = re.compile(r'^(GIR 0AA|%s %s)$' % (outcode_pattern, incode_pattern))
    space_regex = re.compile(r' *(%s)$' % incode_pattern)

    postcode = postcode.upper().strip()

    postcode = space_regex.sub(r' \1', postcode)
    if not postcode_regex.search(postcode):
        return False
    return True

import re

from popolo.models import Identifier

from candidates.models import MembershipExtra


def shorten_post_label(post_label):
    return re.sub(r'^Member of Parliament for ', '', post_label)


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
            raise Exception, message.format(parlparse_id)
        theyworkforyou_url = 'http://www.theyworkforyou.com/mp/{0}'.format(
            m.group(1)
        )
    except Identifier.DoesNotExist:
        pass
    party_ec_id = person.parties[election].get('electoral_commission_id', '')
    candidacy = MembershipExtra.objects.get(
        election=election,
        base__person=person,
        base__role=election.candidate_membership_role,
    ).select_relate('base', 'base__post', 'base__post__area')
    post = candidacy.base.post
    party = candidacy.base.on_behalf_of
    party_ec_id = party.identifiers.get(scheme='electoral-commission').identifier
    return {
        'gss_code': post.area.other_identifiers.get(scheme='gss'),
        'parlparse_id': parlparse_id,
        'theyworkforyou_url': theyworkforyou_url,
        'party_ec_id': party_ec_id
    }

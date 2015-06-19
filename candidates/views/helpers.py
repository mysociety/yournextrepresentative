from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponseRedirect

from slugify import slugify

from ..election_specific import AREA_POST_DATA
from ..models import (
    PopItPerson, membership_covers_date
)

def join_with_commas_and_and(a):
    # FIXME: this is English-specific
    result = ''
    if len(a) >= 3:
        result += u', '.join(a[:-2])
        result += u', '
    result += u', and '.join(a[-2:])
    return result

def get_redirect_to_post(election, post_data):
    short_post_label = AREA_POST_DATA.shorten_post_label(
        election, post_data['label']
    )
    return HttpResponseRedirect(
        reverse(
            'constituency',
            kwargs={
                'election': election,
                'post_id': post_data['id'],
                'ignored_slug': slugify(short_post_label),
            }
        )
    )

def get_people_from_memberships(election_data, memberships):
    current_candidates = set()
    past_candidates = set()
    for membership in memberships:
        if not membership.get('role') == 'Candidate':
            continue
        person = PopItPerson.create_from_dict(membership['person_id'])
        if membership_covers_date(
                membership,
                election_data['election_date']
        ):
            current_candidates.add(person)
        else:
            for election, election_data in settings.ELECTIONS_BY_DATE:
                if not election_data.get('use_for_candidate_suggestions'):
                    continue
                if membership_covers_date(
                        membership,
                        election_data['election_date'],
                ):
                    past_candidates.add(person)

    return current_candidates, past_candidates

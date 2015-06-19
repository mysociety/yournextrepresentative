from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponseRedirect

from slugify import slugify

from ..models import (
    get_post_label_from_post_id, PopItPerson, membership_covers_date
)

def join_with_commas_and_and(a):
    # FIXME: this is English-specific
    result = ''
    if len(a) >= 3:
        result += u', '.join(a[:-2])
        result += u', '
    result += u', and '.join(a[-2:])
    return result

def get_redirect_from_mapit_id(election, mapit_id):
    post_label = get_post_label_from_post_id(mapit_id)
    return HttpResponseRedirect(
        reverse(
            'constituency',
            kwargs={
                'election': election,
                'post_id': mapit_id,
                'ignored_slug': slugify(post_label),
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

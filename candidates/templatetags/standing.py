from __future__ import unicode_literals

from slugify import slugify

from django import template
from django.core.urlresolvers import reverse
from django.db.models import Prefetch
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from popolo.models import Membership

from uk_results.models import CandidateResult

register = template.Library()

@register.filter
def post_in_election(person, election):
    # FIXME: this is inefficient, but similar to the previous
    # implementation.
    try:
        candidacy = person.memberships.prefetch_related(
            Prefetch(
                'result',
                CandidateResult.objects.select_related(
                    'result_set',
                    'result_set__post_result',
                )
            )
        ).get(
            role=election.candidate_membership_role,
            extra__election=election
        )
    except Membership.DoesNotExist:
        candidacy = None

    if candidacy:
        link = '<a href="{cons_url}">{cons_name}</a>'.format(
            cons_url=reverse(
                'constituency',
                kwargs={
                    'election': election.slug,
                    'post_id': candidacy.post.extra.slug,
                    'ignored_slug': slugify(candidacy.post.extra.short_label),
                }
            ),
            cons_name=candidacy.post.extra.short_label
        )
        result = '<span class="constituency-value-standing-link">{0}</span>'.format(
            link
        )
        result += ' <span class="party">{0}</span>'.format(
            candidacy.on_behalf_of.name
        )
        candidate_results = list(candidacy.result.all())
        if candidate_results:
            for candidate_result in candidate_results:
                if candidate_result.result_set.post_result.confirmed:
                    # Then we're OK to display this result:
                    result += '<br>'
                    if candidate_result.is_winner:
                        result += '<span class="candidate-result-confirmed candidate-result-confirmed-elected">Elected!</span>'
                    else:
                        result += '<span class="candidate-result-confirmed candidate-result-confirmed-not-elected">Not elected</span>'
                    result += ' <span class="vote-count">({0} votes)</span>'.format(
                         candidate_result.num_ballots_reported
                    )
                    result += '<br>'

    else:
        if election in person.extra.not_standing.all():
            if election.current:
                result = '<span class="constituency-value-not-standing">%s</span>' % _('Not standing')
            else:
                result = '<span class="constituency-value-not-standing">%s</span>' % _('Did not stand')
        else:
            if election.current:
                result = '<span class="constituency-value-unknown">%s</span>' % _('No information yet')
            else:
                result = '<span class="constituency-not-standing">%s</span>' % _('Did not stand')
    return mark_safe(result)

@register.filter
def election_decision_known(person, election):
    return person.extra.get_elected(election) is not None

@register.filter
def was_elected(person, election):
    return bool(person.extra.get_elected(election))

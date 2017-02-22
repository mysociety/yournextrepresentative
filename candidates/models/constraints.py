from __future__ import unicode_literals

from . import popolo_extra as models

def check_constraints():
    return check_paired_models() + check_membership_elections_consistent()

def check_paired_models():
    errors = []
    for base, extra in (
        (models.Person, models.PersonExtra),
        (models.Organization, models.OrganizationExtra),
        (models.Post, models.PostExtra),
        (models.Area, models.AreaExtra),
        (models.Image, models.ImageExtra),
    ):
        format_kwargs = {'base': base.__name__, 'extra': extra.__name__}
        base_ids = set(
            base.objects.values_list('pk', flat=True))
        base_ids_from_extra = set(
            extra.objects.values_list('base_id', flat=True))
        extra_ids = set(
            extra.objects.values_list('pk', flat=True))
        if len(base_ids) != len(extra_ids):
            msg = 'There were {base_count} {base} objects, but ' \
                  '{extra_count} {extra} objects'
            fmt = format_kwargs.copy()
            fmt.update({
                'base_count': len(base_ids),
                'extra_count': len(extra_ids)})
            errors.append(msg.format(**fmt))
        base_ids_with_no_extra = sorted(base_ids - base_ids_from_extra)
        for base_id in base_ids_with_no_extra:
            msg = 'The {base} object with ID {id} had no corresponding ' \
                  '{extra} object'
            fmt = format_kwargs.copy()
            fmt.update({'id': base_id})
            errors.append(msg.format(**fmt))
        # We could try to check for other errors here, but they are
        # prevented by various constraints. For example, you can't
        # have an *Extra object with no corresponding base object,
        # because the OneToOneField 'base' fields have the default
        # null=False. As a second example, you can't have more than
        # one *Extra object pointing to the same base object because
        # there is a unique constraint on the base_id field.
    return errors

def check_membership_elections_consistent():
    # Any membership with role 'Candidate' should be associated with
    # an election via .extra.election and a post via .post. This
    # election + post combination should also be present in the
    # PostExtraElection join model, but this hadn't previously been
    # enforced. This method checks for that.
    errors = []

    postextra_election_tuples_allowed = \
        set(models.PostExtraElection.objects \
            .values_list('postextra', 'election'))

    for me in models.MembershipExtra.objects.select_related(
            'base__post__extra', 'election', 'base__person'):
        post_extra = me.base.post.extra
        election = me.election
        if (post_extra.id, election.id) not in postextra_election_tuples_allowed:
            errors.append(
                'There was a membership for {person_name} ({person_id}) ' \
                'with post {post_label} ({post_extra_slug}) and election ' \
                '{election_slug} but there\'s no PostExtraElection linking ' \
                'them.'.format(
                    person_name=me.base.person.name,
                    person_id=me.base.person.id,
                    post_label=me.base.post.label,
                    post_extra_slug=post_extra.slug,
                    election_slug=me.election.slug))
    return errors


def check_no_candidancy_for_election(person, election):
    if election.candidacies.filter(
            base__person=person,
            base__role=election.candidate_membership_role).exists():
        msg = 'There was an existing candidacy for {person} ({person_id}) ' \
            'in the election "{election}"'
        raise Exception(msg.format(
            person=person, person_id=person.id, election=election.name))

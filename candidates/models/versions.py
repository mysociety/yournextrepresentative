from __future__ import unicode_literals

from collections import defaultdict
from datetime import datetime
import re

from .fields import ExtraField, SimplePopoloField, ComplexPopoloField

from django.db.models import F

from ..twitter_api import update_twitter_user_id, TwitterAPITokenMissing

# FIXME: handle the extra fields (e.g. cv & program for BF)
# FIXME: check all the preserve_fields are dealt with

def get_person_as_version_data(person):
    from candidates.election_specific import shorten_post_label
    result = {}
    person_extra = person.extra
    result['id'] = str(person.id)
    for field in SimplePopoloField.objects.all():
        result[field.name] = getattr(person, field.name) or ''
    for field in ComplexPopoloField.objects.all():
        result[field.name] = getattr(person_extra, field.name)
    extra_values = {
        extra_value.field.key: extra_value.value
        for extra_value in person.extra_field_values.select_related('field')
    }
    extra_fields = {
        extra_field.key: extra_values.get(extra_field.key, '')
        for extra_field in ExtraField.objects.all()
    }
    if extra_fields:
        result['extra_fields'] = extra_fields
    result['other_names'] = [
        {
            'name': on.name,
            'note': on.note,
            'start_date': on.start_date,
            'end_date': on.end_date,
        }
        for on in person.other_names.order_by('name', 'start_date', 'end_date')
    ]
    identifiers = list(person.identifiers.all())
    if identifiers:
        result['identifiers'] = [
            {
                'scheme': i.scheme,
                'identifier': i.identifier,
            }
            for i in identifiers
        ]
    result['image'] = person.image
    standing_in = {}
    party_memberships = {}
    for membership in person.memberships.filter(post__isnull=False):
        from candidates.models import MembershipExtra
        post = membership.post
        try:
            membership_extra = membership.extra
        except MembershipExtra.DoesNotExist:
            continue
        election = membership_extra.election
        standing_in[election.slug] = {
            'post_id': post.extra.slug,
            'name': shorten_post_label(post.label)
        }
        if membership_extra.elected is not None:
            standing_in[election.slug]['elected'] = membership_extra.elected
        if membership_extra.party_list_position is not None:
            standing_in[election.slug]['party_list_position'] = \
                membership_extra.party_list_position
        party = membership.on_behalf_of
        party_memberships[election.slug] = {
            'id': party.extra.slug,
            'name': party.name,
        }
    for not_standing_in_election in person_extra.not_standing.all():
        standing_in[not_standing_in_election.slug] = None
    result['standing_in'] = standing_in
    result['party_memberships'] = party_memberships
    return result

def revert_person_from_version_data(person, person_extra, version_data, part_of_merge=False):

    from popolo.models import Membership, Organization, Post
    from candidates.models import MembershipExtra, raise_if_unsafe_to_delete

    from elections.models import Election

    for field in SimplePopoloField.objects.all():
        new_value = version_data.get(field.name)
        if new_value:
            setattr(person, field.name, new_value)
        else:
            setattr(person, field.name, '')

    # Remove any old values in complex fields:
    for field in ComplexPopoloField.objects.all():
        related_manager = getattr(person, field.popolo_array)
        type_kwargs = {field.info_type_key: field.info_type}
        related_manager.filter(**type_kwargs).delete()

    # Then recreate any that should be there:
    for field in ComplexPopoloField.objects.all():
        new_value = version_data.get(field.name, '')
        if new_value:
            person_extra.update_complex_field(field, version_data[field.name])

    # Remove any extra field data and create them from the JSON:
    person.extra_field_values.all().delete()
    extra_fields_from_version = version_data.get('extra_fields', {})
    for extra_field in ExtraField.objects.all():
        value = extra_fields_from_version.get(extra_field.key)
        if value is not None:
            person.extra_field_values.create(
                field=extra_field,
                value=value,
            )

    # Other fields to preserve:
    person.image = version_data.get('image')

    # Remove all other names, and recreate:
    person.other_names.all().delete()
    for on in version_data.get('other_names', []):
        person.other_names.create(
            name=on['name'],
            note=on.get('note', ''),
            start_date=on.get('start_date'),
            end_date=on.get('end_date'),
        )

    # Remove all identifiers, and recreate:
    person.identifiers.all().delete()
    for i in version_data.get('identifiers', []):
        person.identifiers.create(
            scheme=i['scheme'],
            identifier=i['identifier'],
        )

    # Remove all candidacies, and recreate:
    for membership in Membership.objects.filter(
        person=person_extra.base,
        role=F('extra__election__candidate_membership_role')
    ):
        # At the moment the merge code has its own way of preserving
        # the uk_results CandidateResult data (see
        # additional_merge_actions), so they will be
        # recreated. (FIXME: omitting this check when merging does
        # mean that we're not checking for other models in the future
        # that may have a foreign key to Membership when doing
        # merges.)
        if not part_of_merge:
            raise_if_unsafe_to_delete(membership)
        membership.delete()
    # Also remove the indications of elections that this person is
    # known not to be standing in:
    person_extra.not_standing.clear()
    for election_slug, standing_in in version_data['standing_in'].items():
        election = Election.objects.get(slug=election_slug)
        # If the value for that election slug is None, then that means
        # the person is known not to be standing:
        if standing_in is None:
            person_extra.not_standing.add(election)
        else:
            # Get the corresponding party membership data:
            party = Organization.objects.get(
                extra__slug=version_data['party_memberships'][election_slug]['id']
            )
            post = Post.objects.get(extra__slug=standing_in['post_id'])
            membership = Membership.objects.create(
                on_behalf_of=party,
                person=person,
                post=post,
                role=election.candidate_membership_role,
            )
            MembershipExtra.objects.create(
                base=membership,
                election=election,
                elected=standing_in.get('elected'),
                party_list_position=standing_in.get('party_list_position'),
            )
    person.save()
    person_extra.save()
    try:
        update_twitter_user_id(person)
    except TwitterAPITokenMissing:
        pass

def version_timestamp_key(version):
    return datetime.strptime(version['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')

def is_a_merge(version):
    m = re.search(
        r'^After merging person (\d+)', version['information_source'])
    if m:
        return m.group(1)
    return None

def get_versions_parent_map(versions_data):
    version_id_to_parent_ids = {}
    if not versions_data:
        return version_id_to_parent_ids
    canonical_person_id = versions_data[0]['data']['id']
    ordered_versions = sorted(versions_data, key=version_timestamp_key)
    person_id_to_ordered_versions = defaultdict(list)
    # Divide all the version with the same ID into separate ordered
    # lists, and record the parent of each version that we get from
    # doing that:
    for version in ordered_versions:
        version_id = version['version_id']
        person_id = version['data']['id']
        versions_for_person_id = person_id_to_ordered_versions[person_id]
        if versions_for_person_id:
            last_version_id = versions_for_person_id[-1]['version_id']
            version_id_to_parent_ids[version_id] = [last_version_id]
        else:
            version_id_to_parent_ids[version_id] = []
        versions_for_person_id.append(version)
    # Now go through looking for versions that represent merges. Note
    # that it's *possible* for someone to create a new version that
    # doesn't represent a merge but which has a information_source
    # message that makes it look like one. We try to raise an
    # exception if this might have happened, by checking that (a) the
    # person ID in the message also has history in this versions array
    # and (b) the number of unique person IDs in the versions is one
    # more than the number of versions that look like merges. We raise
    # an exception in either of these situations.
    number_of_person_ids = len(person_id_to_ordered_versions.keys())
    number_of_merges = 0
    for version in ordered_versions:
        version_id = version['version_id']
        merged_from = is_a_merge(version)
        if merged_from is None:
            continue
        if merged_from not in person_id_to_ordered_versions:
            # This can happen because for some time there was a bug
            # where the history of the secondary person wasn't
            # included on merging; just treat this as any other
            # version in that case.
            continue
        number_of_merges += 1
        last_version_id_of_other = \
            person_id_to_ordered_versions[merged_from][-1]['version_id']
        version_id_to_parent_ids[version_id].append(last_version_id_of_other)
    if (number_of_merges + 1) != number_of_person_ids:
        msg = "It looks like there was a bogus merge version for person " \
              "with ID {person_id}; there were {nm} merge versions and {np} " \
              "person IDs."
        raise Exception(msg.format(
            person_id=canonical_person_id,
            nm=number_of_merges,
            np=number_of_person_ids,
        ))
    return version_id_to_parent_ids

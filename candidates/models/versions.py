from .field_mappings import form_simple_fields, form_complex_fields_locations

from django.db.models import F

# FIXME: handle the extra fields (e.g. cv & program for BF)
# FIXME: check all the preserve_fields are dealt with
# FIXME: make sure party list positions are stored and retrieved
# FIXME: make sure the 'elected' boolean is stored and retrieved

def get_person_as_version_data(person):
    from candidates.election_specific import shorten_post_label
    result = {}
    person_extra = person.extra
    result['id'] = str(person.id)
    for field, null_value in form_simple_fields.items():
        result[field] = getattr(person, field) or null_value
    for field in form_complex_fields_locations:
        result[field] = getattr(person_extra, field)
    result['other_names'] = [
        {
            'name': on.name,
            'note': on.note,
            'start_date': on.start_date,
            'end_date': on.end_date,
        }
        for on in person.other_names.all()
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
        if person_extra.get_elected(election):
            standing_in[election.slug]['elected'] = True
        party = membership.on_behalf_of
        party_memberships[election.slug] = {
            'id': party.extra.slug,
            'name': party.name,
        }
    result['standing_in'] = standing_in
    result['party_memberships'] = party_memberships
    return result

def revert_person_from_version_data(person, person_extra, version_data):

    from popolo.models import Membership, Organization, Post
    from candidates.models import MembershipExtra
    from elections.models import Election

    for field, null_value in form_simple_fields.items():
        new_value = version_data.get(field)
        if new_value:
            setattr(person, field, new_value)
        else:
            setattr(person, field, null_value)

    # Remove any old values in complex fields:
    for location in form_complex_fields_locations.values():
        related_manager = getattr(person, location['sub_array'])
        type_kwargs = {location['info_type_key']: location['info_type']}
        related_manager.filter(**type_kwargs).delete()

    # Then recreate any that should be there:
    for field, location in form_complex_fields_locations.items():
        new_value = version_data.get(field, '')
        if new_value:
            person_extra.update_complex_field(location, version_data[field])

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
        person.identifiers.objects.create(
            scheme=i['scheme'],
            identifier=i['identifier'],
        )

    # Remove all candidacies, and recreate:
    MembershipExtra.objects.filter(
        base__person=person_extra.base,
        base__role=F('election__candidate_membership_role')
    ).delete()
    for election_slug, standing_in in version_data['standing_in'].items():
        election = Election.objects.get(slug=election_slug)
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
        )
    person.save()
    person_extra.save()

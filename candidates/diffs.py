# The functions in this file are to help produce human readable diffs
# between our JSON representation of candidates.

from __future__ import unicode_literals

import re

from django.conf import settings
from django.utils.translation import ugettext as _
from django.http import Http404

import jsonpatch
import jsonpointer

from candidates.models.versions import get_versions_parent_map
from elections.models import Election


def get_descriptive_value(election, attribute, value, leaf):
    """Get a sentence fragment describing someone's status in a particular year

    'attribute' is either "standing_in" or "party_membership", 'election'
    is one of the slugs from the elections table, and 'value' is what would
    be under that year in the 'standing_in' or 'party_memberships'
    dictionary (see the comment at the top of update.py)."""

    try:
        election_data = Election.objects.get_by_slug(election)
        current_election = election_data.current
        election_name = election_data.name
    except Http404:
        # The election slug may have changed since the diff was stored.
        # Assume this is an older election
        current_election = False
        # Use the raw ID here, as it's more useful than nothing.
        election_name = "{0} election".format(election)


    if attribute == 'party_memberships':
        if leaf:
            # In that case, there's only a particular value in the
            # dictionary that's changed:
            if leaf == 'name':
                if current_election:
                    message = _("is known to be standing for the party '{party}' in the {election}")
                else:
                    message = _("was known to be standing for the party '{party}' in the {election}")
                return message.format(party=value, election=election_name)
            elif leaf == 'id':
                if current_election:
                    message = _('is known to be standing for the party with ID {party} in the {election}')
                else:
                    message = _('was known to be standing for the party with ID {party} in the {election}')
                return message.format(party=value, election=election_name)
            else:
                message = _("Unexpected leaf {0} (attribute: {1}, election: {2}")
                raise Exception(message.format(
                    leaf, attribute, election
                ))
        else:
            if current_election:
                message = _('is known to be standing for the party "{party}" in the {election}')
            else:
                message = _('was known to be standing for the party "{party}" in the {election}')
            return message.format(party=value['name'], election=election_name)
    elif attribute == 'standing_in':
        if value is None:
            if current_election:
                message = _('is known not to be standing in the {election}')
            else:
                message = _('was known not to be standing in the {election}')
            return message.format(election=election_name)
        else:
            if leaf:
                if leaf == 'post_id':
                    if current_election:
                        message = _("is known to be standing for the post with ID {post_id} in the {election}")
                    else:
                        message = _("was known to be standing for the post with ID {post_id} in the {election}")
                    return message.format(post_id=value, election=election_name)
                elif leaf == 'mapit_url':
                    if current_election:
                        message = _("is known to be standing in the constituency with MapIt URL {mapit_url} in the {election}")
                    else:
                        message = _("was known to be standing in the constituency with MapIt URL {mapit_url} in the {election}")
                    return message.format(mapit_url=value, election=election_name)
                elif leaf == 'name':
                    if current_election:
                        message = _("is known to be standing in {party} in the {election}")
                    else:
                        message = _("was known to be standing in {party} in the {election}")
                    return message.format(party=value, election=election_name)
                elif leaf == 'elected':
                    if value:
                        return _("was elected in the {election}").format(election=election_name)
                    else:
                        return _("was not elected in the {election}").format(election=election_name)
                elif leaf == 'party_list_position':
                    if value:
                        return _("is at position {list_position} in their party list in the {election}").format(list_position=value, election=election_name)
                    else:
                        return _("has no position in their party list in the {election}").format(election=election_name)
                else:
                    message = _("Unexpected leaf {0} (attribute: {1}, election: {2}")
                    raise Exception(message.format(
                        leaf, attribute, election
                    ))
            else:
                if current_election:
                    message = _('is known to be standing in {party} in the {election}')
                else:
                    message = _('was known to be standing in {party} in the {election}')
                return message.format(party=value['name'], election=election_name)

def explain_standing_in_and_party_memberships(operation, attribute, election, leaf):
    """Set 'value' and 'previous_value' in operation to a readable explanation

    'attribute' is one of 'standing_in' or 'party_memberships'."""

    for key in ('previous_value', 'value'):
        if key not in operation:
            continue
        if election:
            operation[key] = get_descriptive_value(
                election,
                attribute,
                operation[key],
                leaf,
            )
        else:
            clauses = []
            items = (operation[key] or {}).items()
            for election, value in sorted(items, reverse=True):
                clauses.append(get_descriptive_value(
                    election,
                    attribute,
                    value,
                    leaf,
                ))
            operation[key] = _(' and ').join(clauses)

def get_version_diff(from_data, to_data):
    """Calculate the diff (a mangled JSON patch) between from_data and to_data"""

    basic_patch = jsonpatch.make_patch(from_data, to_data)
    result = []
    for operation in sorted(basic_patch, key=lambda o: (o['op'], o['path'])):
        op = operation['op']
        ignore = False
        # We deal with standing_in and party_memberships slightly
        # differently so they can be presented in human-readable form,
        # so match those cases first:
        m = re.search(
            r'(standing_in|party_memberships)(?:/([^/]+))?(?:/(\w+))?',
            operation['path'],
        )
        if op in ('replace', 'remove'):
            operation['previous_value'] = \
                jsonpointer.resolve_pointer(
                    from_data,
                    operation['path'],
                    default=None
                )

        attribute, election, leaf = m.groups() if m else (None, None, None)
        if attribute:
            explain_standing_in_and_party_memberships(operation, attribute, election, leaf)
        if op in ('replace', 'remove'):
            if op == 'replace' and not operation['previous_value']:
                if operation['value']:
                    operation['op'] = 'add'
                else:
                    # Ignore replacing no data with no data:
                    ignore = True
        elif op == 'add':
            # It's important that we don't skip the case where a
            # standing_in value is being set to None, because that's
            # saying 'we *know* they're not standing then'
            if (not operation['value']) and (attribute != 'standing_in'):
                ignore = True
        operation['path'] = re.sub(r'^/', '', operation['path'])
        if not ignore:
            result.append(operation)
        # The operations generated by jsonpatch are incremental, so we
        # need to apply each before going on to parse the next:
        operation['path'] = '/' + operation['path']
        from_data = jsonpatch.apply_patch(from_data, [operation])
    for operation in result:
        operation['path'] = operation['path'].lstrip('/')
    return result

def clean_version_data(data):
    data = data.copy()
    for election_slug, standing_in in data.get('standing_in', {}).items():
        if standing_in:
            standing_in.pop('mapit_url', None)
    # We're not interested in changes of these IDs:
    for i in data.get('identifiers', []):
        i.pop('id', None)
    for on in data.get('other_names', []):
        on.pop('id', None)
    data.pop('last_party', None)
    data.pop('proxy_image', None)
    data.pop('date_of_birth', None)
    return data

def get_parents_version_data(parents, id_to_version):
    if parents:
        return [(p, id_to_version[p]['data']) for p in parents]
    # If there are no parents, then compare to an empty dictionary
    return [(None, {})]

def get_version_diffs(versions):
    """Add a diff to each of an array of version dicts

    The first version is the most recent; the last is the original
    version."""

    id_to_parent_ids = get_versions_parent_map(versions)
    id_to_version = {v['version_id']: v for v in versions}
    result = []
    for v in versions:
        version_id = v['version_id']
        v['parent_version_ids'] = id_to_parent_ids[version_id]
        version_with_diffs = v.copy()
        version_with_diffs['data'] = clean_version_data(
            version_with_diffs['data'])
        version_with_diffs['parent_version_ids'] = id_to_parent_ids[version_id]
        version_with_diffs['diffs'] = [
            {
                'parent_version_id': parent_with_data[0],
                'parent_diff': get_version_diff(
                    clean_version_data(parent_with_data[1]),
                    version_with_diffs['data']
                )
            } for parent_with_data in
            get_parents_version_data(
                id_to_parent_ids[version_id], id_to_version)
        ]
        result.append(version_with_diffs)
    return result

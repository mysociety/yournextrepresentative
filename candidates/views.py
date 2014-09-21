import json
import re

from slumber.exceptions import HttpClientError
from popit_api import PopIt
from slugify import slugify
import requests
from urlparse import urlunsplit

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render
from django.utils.http import urlquote
from django.views.generic import FormView, TemplateView, DeleteView, UpdateView

from .forms import PostcodeForm, CandidacyForm, NewPersonForm, UpdatePersonForm, ConstituencyForm
from .models import (
    PopItPerson, MapItData, get_candidate_list_popit_id,
    get_constituency_name_from_mapit_id, extract_constituency_name,
    simple_fields, complex_fields_locations, all_fields,
    get_person_data_from_dict, get_next_id, update_id,
    candidate_list_name_re
)

class PopItApiMixin(object):

    """This provides helper methods for manipulating data in a PopIt instance"""

    def __init__(self, *args, **kwargs):
        super(PopItApiMixin, self).__init__(*args, **kwargs)
        api_properties = {
            'instance': settings.POPIT_INSTANCE,
            'hostname': settings.POPIT_HOSTNAME,
            'port': settings.POPIT_PORT,
            'api_version': 'v0.1',
            'append_slash': False,
        }
        if settings.POPIT_API_KEY:
            api_properties['api_key'] = settings.POPIT_API_KEY
        else:
            api_properties['user'] = settings.POPIT_USER
            api_properties['password'] = settings.POPIT_PASSWORD
        self.api = PopIt(**api_properties)

    def get_search_url(self, collection, query):
        port = settings.POPIT_PORT
        instance_hostname = settings.POPIT_INSTANCE + \
            '.' + settings.POPIT_HOSTNAME
        if port != 80:
            instance_hostname += ':' + str(port)
        base_search_url = urlunsplit(
            ('http', instance_hostname, '/api/v0.1/search/', '', '')
        )
        return base_search_url + collection + '?q=' + urlquote(query)

    def get_organization(self, organization_id):
        return self.api.organizations(organization_id).get()['result']

    def get_organization_and_members(self, organization_id):
        organization = self.get_organization(organization_id)
        return (
            organization,
            [ m['person_id'] for m in organization.get('memberships', []) ]
        )

    def membership_exists(self, person_id, organization_id):
        _, members = self.get_organization_and_members(organization_id)
        return person_id in members

    def get_area_from_organization(self, organization):
        if organization['classification'] != "Candidate List":
            return None
        m = candidate_list_name_re.search(organization['name'])
        if not m:
            message = "Found a Candidate List with an unparseable name: '{0}'"
            raise Exception(message.format(organization['name']))
        constituency_name = m.group(1)
        mapit_data = MapItData.constituencies_2010_name_map.get(constituency_name)
        if mapit_data is None:
            message = "Couldn't find the constituency: '{0}'"
            raise Exception(message.format(constituency_name))
        url_format = 'http://mapit.mysociety.org/area/{0}'
        return {
            'name': constituency_name,
            'id': url_format.format(mapit_data['id'])
        }

    def create_membership(self, person_id, organization_id,
                          start_date=None, end_date=None):
        properties = {
            'organization_id': organization_id,
            'person_id': person_id,
        }
        if start_date is not None:
            properties['start_date'] = start_date
        if end_date is not None:
            properties['end_date'] = end_date
        area = self.get_area_from_organization(organization)
        if area is not None:
            properties['area'] = area
        self.api.memberships.post(properties)

    def create_membership_if_not_exists(self, person_id, organization_id):
        organization, members = self.get_organization_and_members(organization_id)
        if person_id not in members:
            # Try to create the new membership
            self.create_membership(person_id, organization_id)

    def delete_membership(self, person_id, organization_id):
        candidate_data = self.api.organizations(organization_id).get()['result']
        for m in candidate_data.get('memberships', []):
            if m['person_id'] == person_id:
                self.api.memberships(m['id']).delete()


def get_redirect_from_mapit_id(mapit_id_str):
    constituency_name = get_constituency_name_from_mapit_id(mapit_id_str)
    if constituency_name is None:
        error_url = reverse('finder')
        error_url += '?bad_constituency_id=' + urlquote(mapit_id_str)
        return HttpResponseRedirect(error_url)
    constituency_url = reverse(
        'constituency',
        kwargs={'constituency_name': constituency_name}
    )
    return HttpResponseRedirect(constituency_url)


class ConstituencyPostcodeFinderView(FormView):
    template_name = 'candidates/finder.html'
    form_class = PostcodeForm

    def form_valid(self, form):
        postcode = form.cleaned_data['postcode']
        url = 'http://mapit.mysociety.org/postcode/' + postcode
        r = requests.get(url)
        if r.status_code == 200:
            mapit_result = r.json
            return get_redirect_from_mapit_id(mapit_result['shortcuts']['WMC'])
        else:
            error_url = reverse('finder')
            error_url += '?bad_postcode=' + urlquote(postcode)
            return HttpResponseRedirect(error_url)

    def get_context_data(self, **kwargs):
        context = super(ConstituencyPostcodeFinderView, self).get_context_data(**kwargs)
        context['constituency_form'] = ConstituencyForm()
        bad_postcode = self.request.GET.get('bad_postcode')
        if bad_postcode:
            context['bad_postcode'] = bad_postcode
        bad_constituency_id = self.request.GET.get('bad_constituency_id')
        if bad_constituency_id:
            context['bad_constituency_id'] = bad_constituency_id
        return context


class ConstituencyNameFinderView(FormView):
    template_name = 'candidates/finder.html'
    form_class = ConstituencyForm

    def form_valid(self, form):
        constituency_id = form.cleaned_data['constituency']
        return get_redirect_from_mapit_id(constituency_id)

    def get_context_data(self, **kwargs):
        context = super(ConstituencyNameFinderView, self).get_context_data(**kwargs)
        context['form'] = PostcodeForm()
        context['constituency_form'] = ConstituencyForm()
        return context


def normalize_party_name(original_party_name):
    """Mangle the party name into a normalized form

    >>> normalize_party_name('The Labour Party')
    'labour'
    >>> normalize_party_name('Labour Party')
    'labour'
    >>> normalize_party_name('Labour')
    'labour'
    """
    result = original_party_name.lower()
    result = re.sub(r'^\s*the\s+', '', result)
    result = re.sub(r'\s+party\s*$', '', result)
    return result.strip()


class ConstituencyDetailView(PopItApiMixin, TemplateView):
    template_name = 'candidates/constituency.html'

    def get_context_data(self, **kwargs):
        context = super(ConstituencyDetailView, self).get_context_data(**kwargs)

        constituency_name = kwargs['constituency_name']

        old_candidate_list_id = get_candidate_list_popit_id(constituency_name, 2010)
        new_candidate_list_id = get_candidate_list_popit_id(constituency_name, 2015)

        _, old_candidate_ids = self.get_organization_and_members(old_candidate_list_id)
        _, new_candidate_ids = self.get_organization_and_members(new_candidate_list_id)

        person_id_to_person_data = {
            person_id: PopItPerson.create_from_popit(self.api, person_id)
            for person_id in set(old_candidate_ids + new_candidate_ids)
        }

        context['new_candidate_list_id'] = new_candidate_list_id

        context['candidates_2010'] = [
            (person_id_to_person_data[p_id], p_id in new_candidate_ids)
            for p_id in old_candidate_ids
        ]
        context['candidates_2015'] = [
            person_id_to_person_data[p_id] for p_id in new_candidate_ids
        ]
        context['constituency_name'] = constituency_name

        context['add_candidate_form'] = NewPersonForm()

        return context


class CandidacyMixin(object):

    def get_person_and_organization(self, form):
        # If either of these don't exist, an HttpClientError will be
        # thrown, which is fine for error checking at the moment
        organization_id = form.cleaned_data['organization_id']
        person_id = form.cleaned_data['person_id']
        try:
            organization_data = self.api.organizations(organization_id).get()['result']
            person_data = self.api.persons(person_id).get()['result']
        except HttpClientError as e:
            if e.response.status_code == 404:
                return HttpResponseBadRequest('Unknown organization_id or person_id')
            else:
                raise
        return (person_data, organization_data)

    def redirect_to_constituency_name(self, constituency_name):
        return HttpResponseRedirect(
            reverse('constituency',
                    kwargs={'constituency_name': constituency_name})
        )

    def redirect_to_constituency(self, candidate_list_data):
        constituency_name = extract_constituency_name(candidate_list_data)
        if constituency_name:
            return self.redirect_to_constituency_name(constituency_name)
        else:
            message = "Failed to parse the candidate_list_name '{0}'"
            raise Exception(message.format(candidate_list_name))

    def get_party(self, party_name):
        party_name = re.sub(r'\s+', ' ', party_name).strip()
        search_url = self.get_search_url(
            'organizations',
            'classification:Party AND name:"{0}"'.format(party_name),
        )
        r = requests.get(search_url)
        wanted_party_name = normalize_party_name(party_name)
        for party in r.json['result']:
            if wanted_party_name == normalize_party_name(party['name']):
                return party
        return None

    def set_party_membership(self, original_party_name, person_id):
        # Remove any existing party memberships:
        person = PopItPerson.create_from_popit(self.api, person_id)
        existing_party_memberships = person.get_party_memberships()
        for m in existing_party_memberships:
            self.api.memberships(m).delete()
        # FIXME: if any of those parties now have zero memberships as
        # a result, we should just completely delete the party.

        # Try to get an existing party with that name, if not, create
        # a new one.
        party = self.get_party(original_party_name)
        if not party:
            # Then create a new party:
            party = {
                'id': slugify(party_name),
                'name': party_name,
                'classification': 'Party',
            }
            self.api.organizations.post(party)
        # Create the party membership:
        self.create_membership_if_not_exists(
            person_id,
            party['id']
        )


class CandidacyView(PopItApiMixin, CandidacyMixin, FormView):

    form_class = CandidacyForm

    def form_valid(self, form):
        person_data, organization_data = self.get_person_and_organization(form)
        print json.dumps(person_data, indent=4)
        person_id = person_data['id']
        candidate_list_id = organization_data['id']
        # Check that that membership doesn't already exist:
        self.create_membership_if_not_exists(person_id, candidate_list_id)
        return self.redirect_to_constituency(organization_data)


class CandidacyDeleteView(PopItApiMixin, CandidacyMixin, FormView):

    form_class = CandidacyForm

    def form_valid(self, form):
        person_data, organization_data = self.get_person_and_organization(form)
        person_id = person_data['id']
        candidate_list_id = organization_data['id']
        self.delete_membership(person_id, candidate_list_id)
        return self.redirect_to_constituency(organization_data)

def update_values_in_sub_array(data, location, new_value):
    """Ensure that only a particular value is present in a sub-dict

    This is useful for replacing values nested in sub-objects of JSON
    data.  This is best demonstrated with an example: if we wanted to
    change the homepage URL in a person record, you could do it like
    this:

    >>> person_data = {
    ...     'id': "john-doe",
    ...     'name': "John Doe",
    ...     'email': "john-doe@example.org",
    ...     'links': [
    ...         {
    ...             'note': "wikipedia",
    ...             'url': "http://en.wikipedia.org/wiki/John_Doe"
    ...         },
    ...         {
    ...             'note': "homepage",
    ...             'url': "http://www.geocities.com"
    ...         },
    ...         {
    ...             'note': "homepage",
    ...             'url': "http://oops.duplicate.example.org"
    ...         }
    ...     ],
    ... }
    >>> update_values_in_sub_array(
    ...     person_data,
    ...     {'sub_array': 'links',
    ...      'info_type_key': 'note',
    ...      'info_value_key': 'url',
    ...      'info_type': 'homepage'},
    ...     "http://john.doe.example.org"
    ... )
    >>> print json.dumps(person_data, indent=4) # doctest: +NORMALIZE_WHITESPACE
    {
        "email": "john-doe@example.org",
        "id": "john-doe",
        "links": [
            {
                "note": "wikipedia",
                "url": "http://en.wikipedia.org/wiki/John_Doe"
            },
            {
                "note": "homepage",
                "url": "http://john.doe.example.org"
            }
        ],
        "name": "John Doe"
    }
    """
    new_info = [
        c for c in data.get(location['sub_array'], [])
        if c.get(location['info_type_key']) != location['info_type']
    ]
    new_info.append({
        location['info_type_key']: location['info_type'],
        location['info_value_key']: new_value
    })
    data[location['sub_array']] = new_info

def get_value_from_person_data(field_name, person_data):
    """Extract a value from a Popolo person data object for a form field name

    For example:

    >>> person_data = {
    ...     'id': "john-doe",
    ...     'name': "John Doe",
    ...     'email': "john-doe@example.org",
    ...     'links': [
    ...         {
    ...             'note': "wikipedia",
    ...             'url': "http://en.wikipedia.org/wiki/John_Doe"
    ...         },
    ...         {
    ...             'note': "homepage",
    ...             'url': "http://www.geocities.com"
    ...         },
    ...         {
    ...             'note': "homepage",
    ...             'url': "http://oops.duplicate.example.org"
    ...         }
    ...     ],
    ... }
    >>> get_value_from_person_data('email', person_data)
    'john-doe@example.org'
    >>> get_value_from_person_data('wikipedia_url', person_data)
    'http://en.wikipedia.org/wiki/John_Doe'
    >>> get_value_from_person_data('foo', person_data)
    Traceback (most recent call last):
      ...
    Exception: Unknown field name foo
    >>> get_value_from_person_data('homepage_url', person_data)
    Traceback (most recent call last):
      ...
    Exception: Found multiple 'note: homepage' elements in 'links' of person with ID 'john-doe'
    """

    if field_name in simple_fields:
        return person_data.get(field_name, '')
    if field_name in complex_fields_locations:
        location = complex_fields_locations[field_name]
        sub_array = person_data.get(location['sub_array'], [])
        matching_info = [
            e for e in sub_array
            if e[location['info_type_key']] == location['info_type']
        ]
        if matching_info:
            if len(matching_info) == 1:
                return matching_info[0][location['info_value_key']]
            else:
                message = "Found multiple '{0}: {1}' elements in '{2}' of person with ID '{3}'"
                raise Exception, message.format(
                    location['info_type_key'],
                    location['info_type'],
                    location['sub_array'],
                    person_data['id'],
                )
            pass
        else:
            return ''
    raise Exception, "Unknown field name {0}".format(field_name)

class UpdatePersonView(PopItApiMixin, CandidacyMixin, FormView):
    template_name = 'candidates/person.html'
    form_class = UpdatePersonForm

    def get_initial(self):
        initial_data = super(UpdatePersonView, self).get_initial()
        person = PopItPerson.create_from_popit(
            self.api, self.kwargs['person_id']
        )
        for field_name in all_fields:
            initial_data[field_name] = get_value_from_person_data(
                field_name,
                person.popit_data
            )
        initial_data['party'] = ''
        if person.party:
            initial_data['party'] = person.party['name']
        if person.constituency_2015:
            initial_data['constituency'] = \
                MapItData.constituencies_2010_name_map[
                    extract_constituency_name(person.constituency_2015)
                ]['id']
        initial_data['standing'] = bool(person.constituency_2015)
        return initial_data

    def get_context_data(self, **kwargs):
        context = super(UpdatePersonView, self).get_context_data(**kwargs)

        context['person'] = self.api.persons(
            self.kwargs['person_id']
        ).get()['result']

        return context

    def form_valid(self, form):
        cleaned = form.cleaned_data
        constituency_name = None
        person = PopItPerson.create_from_popit(
            self.api, self.kwargs['person_id']
        )
        if cleaned['standing']:
            constituency_name = get_constituency_name_from_mapit_id(
                cleaned['constituency']
            )
            if not constituency_name:
                message = "Failed to find a constituency with MapIt ID {}"
                raise Exception(message.format(cleaned['constituency']))
            organization_id = 'candidates-2015-{0}'.format(
                slugify(constituency_name)
            )
            self.create_membership_if_not_exists(
                person.id,
                organization_id
            )
        else:
            # Remove any membership of a 2015 candidate list:
            for membership_id in person.get_candidate_list_memberships('2015'):
                self.api.memberships(membership_id).delete()
        person_data = get_person_data_from_dict(form.cleaned_data, generate_id=False)
        # Update that person:
        person_result = self.api.persons(person.id).put(
            person_data
        )
        self.set_party_membership(
            cleaned['party'],
            person.id
        )
        return self.redirect_to_constituency_name(constituency_name)


class NewPersonView(PopItApiMixin, CandidacyMixin, FormView):
    template_name = 'candidates/person.html'
    form_class = NewPersonForm

    def form_valid(self, form):
        cleaned = form.cleaned_data
        # Check that the candidate list organization exists:
        organization_data = self.api.organizations(
            form.cleaned_data['organization_id']
        ).get()['result']
        person_data = get_person_data_from_dict(form.cleaned_data, generate_id=True)
        # Create that person:
        person_result = create_with_id_retries(
            self.api.persons,
            person_data
        )
        # And update their party:
        self.set_party_membership(
            cleaned['party'],
            person_result['result']['id']
        )
        # Create the candidate list membership:
        self.create_membership_if_not_exists(
            person_result['result']['id'],
            organization_data['id'],
        )
        return self.redirect_to_constituency(organization_data)

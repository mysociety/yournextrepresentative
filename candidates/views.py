from datetime import datetime
import json
from random import randint
import re
import sys

from slumber.exceptions import HttpClientError
from popit_api import PopIt
from slugify import slugify
import requests
from urlparse import urlunsplit

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render
from django.utils.http import urlquote
from django.views.generic import FormView, TemplateView, DeleteView, UpdateView, View

from braces.views import LoginRequiredMixin

from .forms import (
    PostcodeForm, NewPersonForm, UpdatePersonForm, ConstituencyForm,
    CandidacyCreateForm, CandidacyDeleteForm
)
from .models import (
    PopItPerson, MapItData, get_candidate_list_popit_id,
    get_constituency_name_from_mapit_id, extract_constituency_name,
    simple_fields, complex_fields_locations, all_fields,
    get_person_data_from_dict, get_next_id, update_id,
    candidate_list_name_re, get_mapit_id_from_mapit_url,
    PartyData
)

from .update import PersonParseMixin, PersonUpdateMixin

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

    def get_area_from_organization(self, organization, mapit_url_key='id'):
        print "got organization:", json.dumps(organization, indent=4)
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
            mapit_url_key: url_format.format(mapit_data['id'])
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
        organization = self.api.organizations(organization_id).get(embed='')['result']
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


def get_redirect_from_mapit_id(mapit_id):
    constituency_name = get_constituency_name_from_mapit_id(mapit_id)
    return HttpResponseRedirect(
        reverse(
            'constituency',
            kwargs={
                'mapit_area_id': mapit_id,
                'ignored_slug': slugify(constituency_name),
            }
        )
    )


class ConstituencyPostcodeFinderView(FormView):
    template_name = 'candidates/finder.html'
    form_class = PostcodeForm

    def form_valid(self, form):
        postcode = form.cleaned_data['postcode']
        url = 'http://mapit.mysociety.org/postcode/' + postcode
        r = requests.get(url)
        if r.status_code == 200:
            mapit_result = r.json()
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

        context['autocomplete_party_url'] = reverse('autocomplete-party')

        context['mapit_area_id'] = mapit_area_id = kwargs['mapit_area_id']
        context['constituency_name'] = constituency_name = \
            get_constituency_name_from_mapit_id(mapit_area_id)

        old_candidate_list_id = get_candidate_list_popit_id(constituency_name, 2010)
        new_candidate_list_id = get_candidate_list_popit_id(constituency_name, 2015)

        _, old_candidate_ids = self.get_organization_and_members(old_candidate_list_id)
        _, new_candidate_ids = self.get_organization_and_members(new_candidate_list_id)

        person_id_to_person_data = {
            person_id: PopItPerson.create_from_popit(self.api, person_id)
            for person_id in set(old_candidate_ids + new_candidate_ids)
        }

        context['candidates_2010_standing_again'] = [
            person_id_to_person_data[p_id]
            for p_id in old_candidate_ids
            if p_id in new_candidate_ids
        ]

        other_candidates_2010 = [
            person_id_to_person_data[p_id]
            for p_id in old_candidate_ids
            if p_id not in new_candidate_ids
        ]

        # Now split those candidates into those that we know aren't
        # standing again, and those that we just don't know about:
        context['candidates_2010_not_standing_again'] = \
            [p for p in other_candidates_2010 if p.not_standing_in_2015]
        context['candidates_2010_might_stand_again'] = \
            [p for p in other_candidates_2010 if not p.not_standing_in_2015]

        context['candidates_2015'] = \
            [person_id_to_person_data[p_id] for p_id in new_candidate_ids]

        context['add_candidate_form'] = NewPersonForm()

        return context


class CandidacyMixin(object):

    def get_person_and_organization(self, form):
        mapit_area_id = form.cleaned_data['mapit_area_id']
        constituency_name = get_constituency_name_from_mapit_id(mapit_area_id)
        # If either of these don't exist, an HttpClientError will be
        # thrown, which is fine for error checking at the moment
        person_id = form.cleaned_data['person_id']
        organization_id = get_candidate_list_popit_id(constituency_name, 2015)
        try:
            organization_data = self.api.organizations(organization_id).get()['result']
            person_data = self.api.persons(person_id).get()['result']
        except HttpClientError as e:
            if e.response.status_code == 404:
                return HttpResponseBadRequest('Unknown organization_id or person_id')
            else:
                raise
        return (person_data, organization_data)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[-1].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_change_metadata(self, request, information_source):
        return {
            'username': request.user.username,
            'ip': self.get_client_ip(request),
            'information_source': information_source,
            'version_id': "{0:016x}".format(randint(0, sys.maxint)),
            'timestamp': datetime.utcnow().isoformat(),
        }

    def redirect_to_constituency_name(self, constituency_name):
        mapit_data = MapItData.constituencies_2010_name_map.get(constituency_name)
        return get_redirect_from_mapit_id(mapit_data['id'])

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
        for party in r.json()['result']:
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
        self.create_party_membership(person_id, party['id'])


class CandidacyView(LoginRequiredMixin, PopItApiMixin, CandidacyMixin, PersonParseMixin, PersonUpdateMixin, FormView):

    form_class = CandidacyCreateForm

    def form_valid(self, form):
        person_data, organization_data = self.get_person_and_organization(form)
        change_metadata = self.get_change_metadata(
            self.request, form.cleaned_data['source']
        )
        our_person = self.get_person(form.cleaned_data['person_id'])
        previous_versions = our_person.pop('versions')

        print "Going to mark this person as *standing*:"
        print json.dumps(our_person, indent=4)

        our_person['standing_in']['2015'] = self.get_area_from_organization(
            organization_data,
            mapit_url_key='mapit_url'
        )
        our_person['party_memberships']['2015'] = our_person['party_memberships']['2010']

        print "... by updating with this data:"
        print json.dumps(our_person, indent=4)

        self.update_person(our_person, change_metadata, previous_versions)
        return get_redirect_from_mapit_id(form.cleaned_data['mapit_area_id'])


class CandidacyDeleteView(LoginRequiredMixin, PopItApiMixin, CandidacyMixin, PersonParseMixin, PersonUpdateMixin, FormView):

    form_class = CandidacyDeleteForm

    def form_valid(self, form):
        person_data, organization_data = self.get_person_and_organization(form)
        change_metadata = self.get_change_metadata(
            self.request, form.cleaned_data['source']
        )
        our_person = self.get_person(form.cleaned_data['person_id'])
        previous_versions = our_person.pop('versions')

        print "Going to mark this person as *not* standing:"
        print json.dumps(our_person, indent=4)

        our_person['standing_in']['2015'] = None
        del our_person['party_memberships']['2015']

        print "... by updating with this data:"
        print json.dumps(our_person, indent=4)

        self.update_person(our_person, change_metadata, previous_versions)
        return get_redirect_from_mapit_id(form.cleaned_data['mapit_area_id'])

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

def get_previous_constituency_name(standing_in):
    for year in reversed(standing_in.keys()):
        if standing_in[year]:
            return standing_in[year]['name']
    return None

def copy_person_form_data(cleaned_data):
    result = cleaned_data.copy()
    # The date is returned as a datetime.date, so if that's set, turn
    # it into a string:
    date_of_birth_date = result['date_of_birth']
    if date_of_birth_date:
        result['date_of_birth'] = str(date_of_birth_date)
    return result


class RevertPersonView(LoginRequiredMixin, PopItApiMixin, CandidacyMixin, PersonParseMixin, PersonUpdateMixin, View):

    http_method_names = [u'post']

    def post(self, request, *args, **kwargs):
        version_id = self.request.POST['version_id']
        person_id = self.kwargs['person_id']
        source = self.request.POST['source']

        our_person = self.get_person(self.kwargs['person_id'])
        previous_versions = our_person.pop('versions')

        data_to_revert_to = None
        for version in previous_versions:
            if version['version_id'] == version_id:
                data_to_revert_to = version['data']

        if not data_to_revert_to:
            message = "Couldn't find the version {0} of person {1}"
            raise Exception(message.format(version_id, person_id))

        change_metadata = self.get_change_metadata(self.request, source)
        self.update_person(data_to_revert_to, change_metadata, previous_versions)

        return HttpResponseRedirect(
            reverse(
                'person-update',
                kwargs={'person_id': person_id}
            )
        )

class UpdatePersonView(LoginRequiredMixin, PopItApiMixin, CandidacyMixin, PersonParseMixin, PersonUpdateMixin, FormView):
    template_name = 'candidates/person.html'
    form_class = UpdatePersonForm

    def get_initial(self):
        initial_data = super(UpdatePersonView, self).get_initial()
        our_person = self.get_person(self.kwargs['person_id'])
        for field_name in all_fields:
            initial_data[field_name] = our_person.get(field_name)
        initial_data['standing'] = bool(our_person['standing_in'].get('2015'))
        if initial_data['standing']:
            party_data_2015 = our_person['party_memberships'].get('2015', {})
            initial_data['party'] = party_data_2015.get('name', '')
            cons_data_2015 = our_person['standing_in'].get('2015', {})
            mapit_url = cons_data_2015.get('mapit_url')
            if mapit_url:
                initial_data['constituency'] = get_mapit_id_from_mapit_url(mapit_url)
        return initial_data

    def get_context_data(self, **kwargs):
        context = super(UpdatePersonView, self).get_context_data(**kwargs)

        context['person'] = self.api.persons(
            self.kwargs['person_id']
        ).get()['result']
        context['autocomplete_party_url'] = reverse('autocomplete-party')

        # Render the JSON in 'versions' nicely:
        for v in context['person'].get('versions', []):
            v['data'] = json.dumps(v['data'], indent=4, sort_keys=True)

        return context

    def form_valid(self, form):
        # First parse that person's data from PopIt into our more
        # usable data structure:

        our_person = self.get_person(self.kwargs['person_id'])
        previous_versions = our_person.pop('versions')

        print "Going to update this person:"
        print json.dumps(our_person, indent=4)

        previous_constituency_name = get_previous_constituency_name(
            our_person['standing_in']
        )

        # Now we need to make any changes to that data structure based
        # on information given in the form.

        data_for_update = copy_person_form_data(form.cleaned_data)

        # Extract some fields that we will deal with separately:
        change_metadata = self.get_change_metadata(
            self.request, data_for_update.pop('source')
        )
        standing = data_for_update.pop('standing')
        constituency_2015_mapit_id = data_for_update.pop('constituency')
        party_2015 = data_for_update.pop('party')

        # Update our representation with data from the form:
        our_person.update(data_for_update)

        if standing:
            constituency_name = get_constituency_name_from_mapit_id(
                constituency_2015_mapit_id
            )
            if not constituency_name:
                message = "Failed to find a constituency with MapIt ID {}"
                raise Exception(message.format(cleaned['constituency']))
            our_person['standing_in']['2015'] = {
                'name': constituency_name,
                'mapit_url': 'http://mapit.mysociety.org/area/{0}'.format(constituency_2015_mapit_id)
            }
            our_person['party_memberships']['2015'] = {'name': party_2015}
        else:
            # If the person is not standing in 2015, record that
            # they're not and remove the party membership for 2015:
            our_person['standing_in']['2015'] = None
            del our_person['party_memberships']['2015']

        print "Going to update that person with this data:"
        print json.dumps(our_person, indent=4)

        self.update_person(our_person, change_metadata, previous_versions)

        if standing:
            return self.redirect_to_constituency_name(constituency_name)
        else:
            if previous_constituency_name:
                return self.redirect_to_constituency_name(previous_constituency_name)
            else:
                return HttpResponseRedirect(reverse('finder'))


class NewPersonView(LoginRequiredMixin, PopItApiMixin, CandidacyMixin, PersonUpdateMixin, FormView):
    template_name = 'candidates/person.html'
    form_class = NewPersonForm

    def form_valid(self, form):
        data_for_creation = copy_person_form_data(form.cleaned_data)

        change_metadata = self.get_change_metadata(
            self.request, data_for_creation.pop('source')
        )
        # Extract these fields, since we'll present them in the
        # standing_in and party_memberships fields.
        party = data_for_creation.pop('party')
        mapit_area_id = data_for_creation.pop('constituency')
        constituency_name = get_constituency_name_from_mapit_id(mapit_area_id)
        organization_id = get_candidate_list_popit_id(constituency_name, 2015)

        data_for_creation['party_memberships'] = {
            '2015': {
                'name': party
            }
        }

        # Check that the candidate list organization exists:
        organization_data = self.api.organizations(
            organization_id
        ).get()['result']

        data_for_creation['standing_in'] = {
            '2015': self.get_area_from_organization(
                organization_data,
                mapit_url_key='mapit_url',
            )
        }

        print "Going to create a new person from this data:"
        print json.dumps(data_for_creation, indent=4)

        self.create_person(data_for_creation, change_metadata)
        return self.redirect_to_constituency(organization_data)

def party_results_key(party_name):
    party_count = PartyData.party_counts_2010.get(party_name, 0)
    return party_count

class AutocompletePartyView(PopItApiMixin, View):

    http_method_names = [u'get']

    def get(self, request, *args, **kwargs):
        query = re.sub(r'\s+', ' ', request.GET.get("term").strip())
        results = []
        results.append(query)
        query_words = query.split()
        if query_words:
            # Assume all words but the final one are complete:
            search_results = []
            complete_words = query_words[:-1]
            final_word = query_words[-1] + '*'
            all_words = complete_words + [final_word]
            # Get search results:
            search_url = self.get_search_url(
                'organizations',
                'classification:Party AND {0}'.format(' AND '.join(all_words))
            )
            r = requests.get(search_url)
            for organization in r.json()['result']:
                search_results.append(organization['name'])
            search_results.sort(reverse=True, key=party_results_key)
            results += search_results

        return HttpResponse(
            json.dumps(results),
            content_type='application/json'
        )

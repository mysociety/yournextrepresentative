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
from django.views.generic import FormView, TemplateView, DeleteView

from .forms import PostcodeForm, CandidacyForm, NewPersonForm, ConstituencyForm
from .models import PopItPerson, MapItData


class PopItApiMixin(object):

    """This provides helper methods for manipulating data in a PopIt instance"""

    def __init__(self, *args, **kwargs):
        super(PopItApiMixin, self).__init__(*args, **kwargs)
        self.api = PopIt(
            instance=settings.POPIT_INSTANCE,
            hostname=settings.POPIT_HOSTNAME,
            port=settings.POPIT_PORT,
            api_version='v0.1',
            user=settings.POPIT_USER,
            password=settings.POPIT_PASSWORD,
            append_slash=False,
        )

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

    def get_members(self, organization_id):
        candidate_data = self.api.organizations(organization_id).get()['result']
        return [ m['person_id'] for m in candidate_data['memberships'] ]

    def membership_exists(self, person_id, organization_id):
        return person_id in self.get_members(organization_id)

    def create_membership_if_not_exists(self, person_id, organization_id):
        if not self.membership_exists(person_id, organization_id):
            # Try to create the new membership
            self.api.memberships.post({
                'organization_id': organization_id,
                'person_id': person_id,
            })

    def delete_membership(self, person_id, organization_id):
        candidate_data = self.api.organizations(organization_id).get()['result']
        for m in candidate_data['memberships']:
            if m['person_id'] == person_id:
                self.api.memberships(m['id']).delete()


def get_candidate_list_popit_id(constituency_name, year):
    """Return the PopIt organization ID for a constituency's candidate list

    >>> get_candidate_list_popit_id('Leeds North East', 2010)
    'candidates-2010-leeds-north-east'
    >>> get_candidate_list_popit_id('Ayr, Carrick and Cumnock', 2015)
    'candidates-2015-ayr-carrick-and-cumnock'
    """
    return 'candidates-{year}-{slugified_name}'.format(
        year=year,
        slugified_name=slugify(constituency_name),
    )

def get_constituency_name_from_mapit_id(mapit_id):
    constituency_data = MapItData.constituencies_2010.get(str(mapit_id))
    if constituency_data:
        return constituency_data['name']
    return None

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

        old_candidate_ids = self.get_members(old_candidate_list_id)
        new_candidate_ids = self.get_members(new_candidate_list_id)

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

    def redirect_to_constituency(self, candidate_list_data):
        m = re.search(
            r'^Candidates for (.*) in \d+$',
            candidate_list_data['name']
        )
        if m:
            constituency_name = m.group(1)
            return HttpResponseRedirect(
                reverse('constituency',
                        kwargs={'constituency_name': constituency_name})
            )
        else:
            message = "Failed to parse the candidate_list_name '{0}'"
            raise Exception(message.format(candidate_list_name))

    def get_party(self, party_name):
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


def get_person_data_from_form(form, existing_data=None):
    if existing_data is None:
        result = {}
    else:
        result = existing_data
    cleaned = form.cleaned_data
    # First deal with fields that simply map to top level fields in
    # Popolo.
    for field_name in ('name', 'email', 'date_of_birth'):
        if cleaned[field_name]:
            result[field_name] = unicode(cleaned[field_name])
    result['id'] = slugify(result['name'])
    for link_type, field_name in (
        ('wikipedia', 'wikipedia_url'),
        ('homepage', 'homepage_url'),
    ):
        if cleaned[field_name]:
            # Remove any existing links of that type:
            new_links = [
                l for l in result.get('links', [])
                if l.get('note') != link_type
            ]
            new_links.append({
                'note': link_type,
                'url': cleaned[field_name]
            })
            result['links'] = new_links
    # FIXME: do some DRY refactoring with this and the loop above
    for contact_type, field_name in (
        ('twitter', 'twitter_username'),
    ):
        if cleaned[field_name]:
            new_contacts = [
                c for c in result.get('contact_details', [])
                if c.get('type') != contact_type
            ]
            new_contacts.append({
                'type': contact_type,
                'value': cleaned[field_name]
            })
            result['contact_details'] = new_contacts
    return result


class NewPersonView(PopItApiMixin, CandidacyMixin, FormView):
    template_name = 'candidates/person.html'
    form_class = NewPersonForm

    def form_valid(self, form):
        cleaned = form.cleaned_data
        # Check that the candidate list organization exists:
        organization_data = self.api.organizations(
            form.cleaned_data['organization_id']
        ).get()['result']
        # Try to get an existing party with that name, if not, create
        # a new one.
        party_name = cleaned['party']
        party_name = re.sub(r'\s+', ' ', party_name).strip()
        party = self.get_party(party_name)
        if not party:
            # Then create a new party:
            party = {
                'id': slugify(party_name),
                'name': party_name,
                'classification': 'Party',
            }
            self.api.organizations.post(party)
        person_data = get_person_data_from_form(form)
        # Create that person:
        person_result = self.api.persons.post(person_data)
        # Create the party membership:
        self.create_membership_if_not_exists(
            person_result['result']['id'],
            party['id']
        )
        # Create the candidate list membership:
        self.create_membership_if_not_exists(
            person_result['result']['id'],
            organization_data['id'],
        )
        return self.redirect_to_constituency(organization_data)

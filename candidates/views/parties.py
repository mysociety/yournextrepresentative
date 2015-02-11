from django.http import Http404
from django.views.generic import TemplateView

import requests
from slugify import slugify

from ..popit import PopItApiMixin, popit_unwrap_pagination
from ..static_data import MapItData, PartyData

def get_ec_identifier(party):
    result = None
    for identifier in party.get('identifiers', []):
        if identifier['scheme'] == 'electoral-commission':
            result = identifier['identifier']
            break
    return result


class PartyListView(PopItApiMixin, TemplateView):
    template_name = 'candidates/party-list.html'

    def get_context_data(self, **kwargs):
        context = super(PartyListView, self).get_context_data(**kwargs)
        parties = []
        for party in popit_unwrap_pagination(
            self.api.organizations,
            embed='',
            per_page=100
        ):
            if party.get('classification') == 'Party':
                parties.append((party['name'], party['id']))
        parties.sort()
        context['parties'] = parties
        return context


class PartyDetailView(PopItApiMixin, TemplateView):
    template_name = 'candidates/party.html'

    def get_context_data(self, **kwargs):
        context = super(PartyDetailView, self).get_context_data(**kwargs)
        party_id = kwargs['organization_id']
        party_name = PartyData.party_id_to_name.get(party_id)
        if not party_name:
            raise Http404("Party not found")
        party = self.api.organizations(party_id).get(embed='')['result']
        party_ec_id = get_ec_identifier(party)
        context['oec_url'] = None
        if party_ec_id:
            context['oec_url'] = \
                'http://openelectoralcommission.org.uk/parties/{0}/{1}/'.format(
                    party_ec_id, slugify(party_name)
                )
        # Make the party emblems conveniently available in the context too:
        context['emblems'] = [
            (i['notes'], i['url'])
            for i in party.get('images', [])
        ]
        countries = ('England', 'Northern Ireland', 'Scotland', 'Wales')
        by_country = {c: {} for c in countries}
        url = self.get_search_url(
            'persons',
            'party_memberships.2015.name:"{0}"'.format(party_name),
            per_page=100
        )
        while url:
            page_result = requests.get(url).json()
            next_url = page_result.get('next_url')
            url = next_url if next_url else None
            for person in page_result['result']:
                standing_in = person.get('standing_in')
                if not (standing_in and standing_in.get('2015')):
                    continue
                mapit_area_id = standing_in['2015'].get('post_id')
                mapit_data = MapItData.constituencies_2010.get(mapit_area_id)
                if not mapit_data:
                    continue
                by_country[mapit_data['country_name']][mapit_area_id] = {
                    'person_id': person['id'],
                    'person_name': person['name'],
                    'post_id': mapit_area_id,
                    'constituency_name': mapit_data['name']
                }
        context['party_name'] = party_name
        context['register'] = party['register']
        if context['register'] == 'Northern Ireland':
            relevant_countries = ('Northern Ireland')
        else:
            relevant_countries = ('England', 'Scotland', 'Wales')
        candidates_by_country = {}
        for country in relevant_countries:
            candidates_by_country[country] = None
            if by_country[country]:
                candidates_by_country[country] = \
                    [
                        (c[0], c[1], by_country[country].get(c[0]))
                        for c in MapItData.constituencies_2010_by_country[country]
                    ]
        context['candidates_by_country'] = sorted(
            candidates_by_country.items(),
            key=lambda k: k[0]
        )
        return context

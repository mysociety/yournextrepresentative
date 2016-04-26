import requests
from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand

from uk_results.models import Council
from uk_results import constants


class Command(BaseCommand):
    def handle(self, **options):
        for council_type in constants.COUNCIL_TYPES:
            self.get_type_from_mapit(council_type)

    def get_contact_info_from_gov_uk(self, council_id):
        req = requests.get("%s%s" % (constants.GOV_UK_LA_URL, council_id))
        soup = BeautifulSoup(req.text)
        info = {}
        article = soup.findAll('article')[0]
        info['website'] = article.find(id='url')['href'].strip()
        info['email'] = article.find(
            id='authority_email').a['href'].strip()[7:]
        info['phone'] = article.find(id='authority_phone').text.strip()[7:]
        info['address'] = "\n".join(
            article.find(id='authority_address').stripped_strings)
        info['postcode'] = article.find(id='authority_postcode').text
        return info

    def get_type_from_mapit(self, council_type):
        req = requests.get('%sareas/%s' % (constants.MAPIT_URL, council_type))
        for mapit_id, council in list(req.json().items()):
            council_id = council['codes'].get('gss')
            if not council_id:
                council_id = council['codes'].get('ons')
            print(council_id)
            contact_info = {
                'name': council['name'],
            }
            if council_type != "LGD":
                contact_info.update(
                    self.get_contact_info_from_gov_uk(council_id))
            council, created = Council.objects.update_or_create(
                pk=council_id,
                mapit_id=mapit_id,
                council_type=council_type,
                defaults=contact_info,
            )

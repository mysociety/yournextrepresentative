from collections import defaultdict
from datetime import date
import re

from slumber.exceptions import HttpServerError

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from candidates.popit import create_popit_api_object, popit_unwrap_pagination

def fix_joint_party_name(joint_party_name):
    return {
        'The Christian Party Christian Peoples Alliance':
        'Christian Party Christian Peoples Alliance'
    }.get(joint_party_name, joint_party_name)

def extract_number_from_id(party_id):
    m = re.search('\d+', party_id)
    if m:
        return int(m.group(0), 10)
    return -1

def create_or_update_party(api, joint_party_name, sub_parties):
    party_ids = sorted(
        extract_number_from_id(p['id'])
        for p in sub_parties
    )
    registers = set(p['register'] for p in sub_parties)
    if len(registers) > 1:
        raise Exception("Multiple registers found " + repr(registers))
    joint_party_id = 'joint-party:' + '-'.join(str(i) for i in party_ids)
    party_data = {
        'id': joint_party_id,
        'name': joint_party_name,
        'slug': slugify(joint_party_name),
        'classification': 'Party',
        'descriptions': [],
        'dissolution_date': '9999-12-31',
        'register': next(iter(registers)),
    }
    try:
        api.organizations.post(party_data)
    except HttpServerError as e:
        if 'E11000' in e.content:
            # Duplicate Party Found
            api.organizations(joint_party_id).put(party_data)
        else:
            raise

joint_description_re = re.compile(
    r'^(?P<joint_name>.*?) \([jJ]oint [dD]escriptions? with (?P<sub_party>.*)\)'
)


class Command(BaseCommand):
    help = "Create joint pseudo-parties based on parties with joint descriptions"

    def handle(self, **options):
        joint_party_to_sub_parties = defaultdict(list)
        api = create_popit_api_object()
        for party in popit_unwrap_pagination(
                api.organizations,
                embed='',
                per_page=200
        ):
            if party['classification'] != 'Party':
                continue
            if 'dissolution_date' in party:
                dissolution_date = party['dissolution_date']
                if dissolution_date < str(date.today()):
                    continue
            for d in party.get('descriptions', []):
                m = joint_description_re.search(d['description'])
                if not m:
                    continue
                joint_name = fix_joint_party_name(m.group('joint_name'))
                joint_party_to_sub_parties[joint_name].append(party)
        for joint_name, sub_parties in joint_party_to_sub_parties.items():
            if len(sub_parties) < 2:
                message = 'Ignoring "{joint_name}" (only made up of one party: "{sub_party}")'
                print message.format(
                    joint_name=joint_name,
                    sub_party=sub_parties[0]['name']
                )
                continue
            create_or_update_party(api, joint_name, sub_parties)

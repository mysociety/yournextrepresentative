# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
from mock import patch
from string import Template

from django.db.models import F

from django_webtest import WebTest
from popolo.models import Identifier

from candidates.models import MembershipExtra, PersonExtra, ExtraField

from compat import bytes_to_unicode

from .auth import TestUserMixin
from .settings import SettingsMixin
from .uk_examples import UK2015ExamplesMixin
from . import factories

example_timestamp = '2014-09-29T10:11:59.216159'
example_version_id = '5aa6418325c1a0bb'

# FIXME: add a test to check that unauthorized people can't revert

class TestRevertPersonView(TestUserMixin, SettingsMixin, UK2015ExamplesMixin, WebTest):

    version_template = Template('''[
          {
            "username": "symroe",
            "information_source": "Just adding example data",
            "ip": "127.0.0.1",
            "version_id": "35ec2d5821176ccc",
            "timestamp": "2014-10-28T14:32:36.835429",
            "data": {
              "name": "Tessa Jowell",
              "id": "2009",
              "twitter_username": "",
              "standing_in": {
                "2010": {
                  "post_id": "65808",
                  "name": "Dulwich and West Norwood",
                  "mapit_url": "http://mapit.mysociety.org/area/65808"
                },
                "2015": {
                  "post_id": "65808",
                  "name": "Dulwich and West Norwood",
                  "mapit_url": "http://mapit.mysociety.org/area/65808"
                }
              },
              "homepage_url": "",
              "birth_date": null,
              "wikipedia_url": "https://en.wikipedia.org/wiki/Tessa_Jowell",
              "party_memberships": {
                "2010": {
                  "id": "$slug",
                  "name": "Labour Party"
                },
                "2015": {
                  "id": "$slug",
                  "name": "Labour Party"
                }
              },
              "identifiers": [
                {
                  "identifier": "uk.org.publicwhip/person/10326",
                  "scheme": "uk.org.publicwhip"
                },
                {
                  "identifier": "2959",
                  "scheme": "yournextmp-candidate"
                }
              ],
              "email": "jowell@example.com",
              "extra_fields": {
                "cv": "http://example.org/cv.doc",
                "notes": "Some updated notes here"
              }
            }
          },
          {
            "username": "mark",
            "information_source": "An initial version",
            "ip": "127.0.0.1",
            "version_id": "5469de7db0cbd155",
            "timestamp": "2014-10-01T15:12:34.732426",
            "data": {
              "name": "Tessa Jowell",
              "id": "2009",
              "twitter_username": "",
              "standing_in": {
                "2010": {
                  "post_id": "65808",
                  "name": "Dulwich and West Norwood",
                  "mapit_url": "http://mapit.mysociety.org/area/65808"
                }
              },
              "homepage_url": "http://example.org/tessajowell",
              "birth_date": "1947-09-17",
              "wikipedia_url": "",
              "party_memberships": {
                "2010": {
                  "id": "$slug",
                  "name": "Labour Party"
                }
              },
              "identifiers": [
                {
                  "identifier": "uk.org.publicwhip/person/10326",
                  "scheme": "uk.org.publicwhip"
                },
                {
                  "identifier": "2959",
                  "scheme": "yournextmp-candidate"
                }
              ],
              "email": "tessa.jowell@example.com",
              "extra_fields": {
                "cv": "",
                "notes": "Some original notes here"
              }
            }
          }
        ]
    ''')

    def setUp(self):
        super(TestRevertPersonView, self).setUp()
        person_extra = factories.PersonExtraFactory.create(
            base__id=2009,
            base__name='Tessa Jowell',
            base__email='jowell@example.com',
            versions=self.version_template.substitute(
                slug=self.labour_party_extra.slug
            )
        )
        person_extra.base.links.create(
            url='',
            note='wikipedia',
        )
        factories.CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base
        )
        factories.CandidacyExtraFactory.create(
            election=self.earlier_election,
            base__person=person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base
        )
        ExtraField.objects.create(
            type='url',
            key='cv',
            label='CV or Resumé',
        )
        ExtraField.objects.create(
            type='longer-text',
            key='notes',
            label='Notes',
        )

    @patch('candidates.views.version_data.get_current_timestamp')
    @patch('candidates.views.version_data.create_version_id')
    def test_revert_to_earlier_version(
            self,
            mock_create_version_id,
            mock_get_current_timestamp,
    ):
        mock_get_current_timestamp.return_value = example_timestamp
        mock_create_version_id.return_value = example_version_id

        response = self.app.get('/person/2009/update', user=self.user)
        revert_form = response.forms['revert-form-5469de7db0cbd155']
        revert_form['source'] =  'Reverting to version 5469de7db0cbd155 for testing purposes'
        response = revert_form.submit()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, 'http://localhost:80/person/2009')

        # Now get the person from the database and check if the
        # details are the same as the earlier version:
        person_extra = PersonExtra.objects.get(base__id=2009)

        # First check that a new version has been created:
        new_versions = json.loads(person_extra.versions)

        self.maxDiff = None
        expected_new_version = {
            'data': {
                'facebook_page_url': '',
                'facebook_personal_url': '',
                'name': 'Tessa Jowell',
                'honorific_suffix': '',
                'party_ppc_page_url': '',
                'gender': '',
                'image': None,
                'linkedin_url': '',
                'id': '2009',
                'other_names': [],
                'honorific_prefix': '',
                'standing_in': {
                    '2010':
                    {
                        'post_id': '65808',
                        'name': 'Dulwich and West Norwood',
                    }
                },
                'homepage_url': 'http://example.org/tessajowell',
                'twitter_username': '',
                'wikipedia_url': '',
                'party_memberships': {
                    '2010': {
                        'id': self.labour_party_extra.slug,
                        'name': 'Labour Party'
                    }
                },
                'birth_date': '1947-09-17',
                'identifiers': [
                    {
                        'identifier': '2959',
                        'scheme': 'yournextmp-candidate'
                    },
                    {
                        'identifier': 'uk.org.publicwhip/person/10326',
                        'scheme': 'uk.org.publicwhip'
                    },
                ],
                'email': 'tessa.jowell@example.com',
                'extra_fields': {
                    'cv': '',
                    'notes': 'Some original notes here'
                }
            },
            'information_source': 'Reverting to version 5469de7db0cbd155 for testing purposes',
            'timestamp': '2014-09-29T10:11:59.216159',
            'username': 'john',
            'version_id': '5aa6418325c1a0bb'
        }

        self.assertEqual(new_versions[0], expected_new_version)

        self.assertEqual(person_extra.base.birth_date, '1947-09-17')
        self.assertEqual(person_extra.homepage_url, 'http://example.org/tessajowell')

        extra_values = list(person_extra.base.extra_field_values \
            .order_by('field__key') \
            .values('field__key', 'value'))
        self.assertEqual(
            extra_values,
            [
                {
                    'field__key': 'cv',
                    'value': ''
                },
                {
                    'field__key': 'notes',
                    'value': 'Some original notes here'
                },
            ]
        )

        candidacies = MembershipExtra.objects.filter(
            base__person=person_extra.base,
            base__role=F('election__candidate_membership_role')
        ).order_by('election__election_date')

        self.assertEqual(len(candidacies), 1)
        self.assertEqual(candidacies[0].election.slug, '2010')

        # The homepage link should have been added and the Wikipedia
        # one removed:
        self.assertEqual(1, person_extra.base.links.count())
        remaining_link = person_extra.base.links.first()
        self.assertEqual(remaining_link.note, 'homepage')

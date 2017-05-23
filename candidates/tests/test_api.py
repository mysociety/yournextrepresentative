from __future__ import unicode_literals

from datetime import datetime
import json
from mock import call, patch
import os
from os.path import exists, join
from shutil import rmtree
from tempfile import mkdtemp

from django.core.management import call_command

from django_webtest import WebTest

from .factories import (
    AreaExtraFactory, CandidacyExtraFactory, MembershipFactory,
    PersonExtraFactory, PostExtraFactory,
)
from .uk_examples import UK2015ExamplesMixin

from candidates.management.commands.candidates_cache_api_to_directory \
    import prune
from candidates.models import LoggedAction, PersonRedirect


class TestAPI(UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestAPI, self).setUp()

        person_extra = PersonExtraFactory.create(
            base__id='2009',
            base__name='Tessa Jowell'
        )
        dulwich_not_stand = PersonExtraFactory.create(
            base__id='4322',
            base__name='Helen Hayes'
        )
        edinburgh_candidate = PersonExtraFactory.create(
            base__id='818',
            base__name='Sheila Gilmore'
        )
        edinburgh_winner = PersonExtraFactory.create(
            base__id='5795',
            base__name='Tommy Sheppard'
        )
        edinburgh_may_stand = PersonExtraFactory.create(
            base__id='5163',
            base__name='Peter McColl'
        )

        CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base
            )
        MembershipFactory.create(
            person=person_extra.base,
            organization=self.labour_party_extra.base
        )

        CandidacyExtraFactory.create(
            election=self.earlier_election,
            base__person=dulwich_not_stand.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base,
            )
        dulwich_not_stand.not_standing.add(self.election)

        CandidacyExtraFactory.create(
            election=self.election,
            base__person=edinburgh_winner.base,
            base__post=self.edinburgh_east_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base,
            elected=True,
            )

        CandidacyExtraFactory.create(
            election=self.election,
            base__person=edinburgh_candidate.base,
            base__post=self.edinburgh_east_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base
            )
        MembershipFactory.create(
            person=edinburgh_candidate.base,
            organization=self.labour_party_extra.base
        )

        MembershipFactory.create(
            person=edinburgh_winner.base,
            organization=self.labour_party_extra.base
        )
        CandidacyExtraFactory.create(
            election=self.earlier_election,
            base__person=edinburgh_may_stand.base,
            base__post=self.edinburgh_east_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base
            )

    def test_api_basic_response(self):
        response = self.app.get(
            '/api/v0.9/'
        )
        self.assertEqual(response.status_code, 200)
        json = response.json

        self.assertEqual(
            json['persons'],
            'http://localhost:80/api/v0.9/persons/'
        )
        self.assertEqual(json['areas'], 'http://localhost:80/api/v0.9/areas/')
        self.assertEqual(
            json['organizations'],
            'http://localhost:80/api/v0.9/organizations/'
        )
        self.assertEqual(
            json['elections'],
            'http://localhost:80/api/v0.9/elections/'
        )
        self.assertEqual(json['posts'], 'http://localhost:80/api/v0.9/posts/')

        persons_resp = self.app.get('/api/v0.9/persons/')
        self.assertEqual(persons_resp.status_code, 200)

        areas_resp = self.app.get('/api/v0.9/areas/')
        self.assertEqual(areas_resp.status_code, 200)

        organizations_resp = self.app.get('/api/v0.9/organizations/')
        self.assertEqual(organizations_resp.status_code, 200)

        elections_resp = self.app.get('/api/v0.9/elections/')
        self.assertEqual(elections_resp.status_code, 200)

        posts_resp = self.app.get('/api/v0.9/posts/')
        self.assertEqual(posts_resp.status_code, 200)

    def test_api_errors(self):
        response = self.app.get(
            '/api/',
            expect_errors=True
        )
        self.assertEqual(response.status_code, 404)

        response = self.app.get(
            '/api/v0.8',
            expect_errors=True
        )
        self.assertEqual(response.status_code, 404)

        response = self.app.get(
            '/api/v0.9/person/',
            expect_errors=True
        )
        self.assertEqual(response.status_code, 404)

        response = self.app.get(
            '/api/v0.9/persons/4000/',
            expect_errors=True
        )
        self.assertEqual(response.status_code, 404)

        response = self.app.post(
            '/api/v0.9/persons/',
            {},
            expect_errors=True
        )
        self.assertEqual(response.status_code, 403)

    def test_api_persons(self):
        persons_resp = self.app.get('/api/v0.9/persons/')

        persons = persons_resp.json

        self.assertEqual(persons['count'], len(persons['results']))
        self.assertEqual(persons['count'], 5)

    def test_api_person(self):
        person_resp = self.app.get('/api/v0.9/persons/2009/')

        self.assertEqual(person_resp.status_code, 200)

        person = person_resp.json
        self.assertEqual(person['id'], 2009)
        self.assertEqual(person['name'], 'Tessa Jowell')

        memberships = sorted(
            person['memberships'],
            key=lambda m: m['role']
        )

        self.assertEqual(len(memberships), 2)
        self.assertEqual(memberships[1]['role'], 'Candidate')

        self.assertEqual(len(person['versions']), 0)

    def test_api_areas(self):
        areas_resp = self.app.get('/api/v0.9/areas/')

        areas = areas_resp.json

        self.assertEqual(areas['count'], len(areas['results']))
        self.assertEqual(areas['count'], 4)

    def test_api_area(self):
        areas_resp = self.app.get('/api/v0.9/areas/')
        areas = areas_resp.json

        area_id = 0
        for area in areas['results']:
            if area['identifier'] == '65808':
                area_id = area['id']
                break

        area_url = '/api/v0.9/areas/{0}/'.format(area_id)
        area_resp = self.app.get(area_url)
        self.assertEqual(area_resp.status_code, 200)

        area = area_resp.json
        self.assertEqual(area['identifier'], '65808')
        self.assertEqual(area['name'], 'Dulwich and West Norwood')
        self.assertEqual(area['type']['name'], 'WMC')

    def test_api_organizations(self):
        organizations_resp = self.app.get('/api/v0.9/organizations/')

        organizations = organizations_resp.json

        self.assertEqual(organizations['count'], len(organizations['results']))
        self.assertEqual(organizations['count'], 7)

    def test_api_organization(self):
        organizations_resp = self.app.get('/api/v0.9/organizations/')
        organizations = organizations_resp.json

        organization_url = None
        for organization in organizations['results']:
            if organization['id'] == 'party:53':
                organization_url = organization['url']
                break

        organization_resp = self.app.get(organization_url)
        self.assertEqual(organization_resp.status_code, 200)

        organization = organization_resp.json
        self.assertEqual(organization['id'], 'party:53')
        self.assertEqual(organization['name'], 'Labour Party')

    def test_api_elections(self):
        elections_resp = self.app.get('/api/v0.9/elections/')

        elections = elections_resp.json

        self.assertEqual(elections['count'], len(elections['results']))
        self.assertEqual(elections['count'], 3)

    def test_api_election(self):
        elections_resp = self.app.get('/api/v0.9/elections/')
        elections = elections_resp.json

        election_url = None
        for election in elections['results']:
            if election['id'] == '2015':
                election_url = election['url']
                break

        election_resp = self.app.get(election_url)
        self.assertEqual(election_resp.status_code, 200)

        election = election_resp.json
        self.assertEqual(election['id'], '2015')
        self.assertEqual(election['name'], '2015 General Election')

    def test_api_posts(self):
        posts_resp = self.app.get('/api/v0.9/posts/')

        posts = posts_resp.json

        self.assertEqual(posts['count'], len(posts['results']))
        self.assertEqual(posts['count'], 5)

    def test_api_post(self):
        posts_resp = self.app.get('/api/v0.9/posts/')
        posts = posts_resp.json

        post_url = None
        for post in posts['results']:
            if post['id'] == '65808':
                post_url = post['url']
                break

        self.assertTrue(post_url)
        post_resp = self.app.get(post_url)
        self.assertEqual(post_resp.status_code, 200)

        post = post_resp.json

        self.assertEqual(post['id'], '65808')
        self.assertEqual(
            post['label'],
            'Member of Parliament for Dulwich and West Norwood'
        )

    def test_api_person_redirects(self):
        PersonRedirect.objects.create(old_person_id='1234', new_person_id='42')
        PersonRedirect.objects.create(old_person_id='5678', new_person_id='12')
        person_redirects_resp = self.app.get('/api/v0.9/person_redirects/')
        person_redirects = person_redirects_resp.json
        self.assertEqual(
            person_redirects['results'][0]['old_person_id'], 1234)
        self.assertEqual(
            person_redirects['results'][0]['new_person_id'], 42)
        self.assertEqual(
            person_redirects['results'][1]['old_person_id'], 5678)
        self.assertEqual(
            person_redirects['results'][1]['new_person_id'], 12)

    def test_api_person_redirect(self):
        PersonRedirect.objects.create(old_person_id='1234', new_person_id='42')
        url = '/api/v0.9/person_redirects/1234/'
        person_redirect_resp = self.app.get(url)
        person_redirect = person_redirect_resp.json
        self.assertEqual(person_redirect['old_person_id'], 1234)
        self.assertEqual(person_redirect['new_person_id'], 42)

    def test_api_version_info(self):
        version_resp = self.app.get('/version.json')
        self.assertEqual(version_resp.status_code, 200)

        info = version_resp.json
        self.assertEqual(info['users_who_have_edited'], 0)
        self.assertEqual(info['interesting_user_actions'], 0)

        LoggedAction.objects.create(
            action_type='set-candidate-not-elected'
        )

        LoggedAction.objects.create(
            action_type='edit-candidate'
        )

        version_resp = self.app.get('/version.json')
        info = version_resp.json
        self.assertEqual(info['interesting_user_actions'], 1)

    def test_api_cors_headers(self):
        resp = self.app.get('/api/v0.9/', headers={
            'Origin': b'http://example.com'}
        )
        self.assertTrue('Access-Control-Allow-Origin' in resp.headers)
        self.assertEqual(resp.headers['Access-Control-Allow-Origin'], '*')

        resp = self.app.get('/', headers={
            'Origin': b'http://example.com'}
        )
        self.assertFalse('Access-Control-Allow-Origin' in resp.headers)

    def test_api_jsonp_response(self):
        response = self.app.get(
            '/api/v0.9/?format=jsonp&callback=test'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.text.startswith('test('))

    @patch('candidates.management.commands.candidates_cache_api_to_directory.datetime')
    def test_persons_api_to_directory(self, mock_datetime):
        # current
        # timestamped
        # timestamped
        mock_datetime.now.return_value = datetime(2017, 5, 14, 12, 33, 5, 0)
        target_directory = mkdtemp()
        try:
            call_command(
                'candidates_cache_api_to_directory',
                target_directory,
                'https://example.com/media/api-cache-for-wcivf',
                page_size='3',
            )
            expected_leafname = '2017-05-14T12:33:05'
            expected_timestamped_directory = \
                join(target_directory, expected_leafname)
            expected_symlink = join(target_directory, 'latest')
            self.assertTrue(exists(expected_timestamped_directory))
            self.assertTrue(exists(expected_symlink))
            # Check that the symlink points to to the timestamped directory:
            self.assertEqual(os.readlink(expected_symlink), expected_leafname)
            # Check that the files in that directory are as expected:
            entries = os.listdir(expected_timestamped_directory)
            persons_1_leafname = 'persons-000001.json'
            persons_2_leafname = 'persons-000002.json'
            posts_1_leafname = 'posts-000001.json'
            posts_2_leafname = 'posts-000002.json'
            self.assertEqual(set(entries), {
                persons_1_leafname, persons_2_leafname,
                posts_1_leafname, posts_2_leafname,
            })
            # Get the data from those pages:
            with open(join(expected_timestamped_directory, persons_1_leafname)) as f:
                persons_1_data = json.load(f)
            with open(join(expected_timestamped_directory, persons_2_leafname)) as f:
                persons_2_data = json.load(f)
            with open(join(expected_timestamped_directory, posts_1_leafname)) as f:
                posts_1_data = json.load(f)
            with open(join(expected_timestamped_directory, posts_2_leafname)) as f:
                posts_2_data = json.load(f)
            # Check the previous and next links are as we expect:
            self.assertEqual(
                persons_1_data['next'],
                'https://example.com/media/api-cache-for-wcivf/{0}/{1}'.format(
                    expected_leafname, persons_2_leafname))
            self.assertEqual(persons_1_data['previous'], None)
            self.assertEqual(persons_2_data['next'], None)
            self.assertEqual(
                persons_2_data['previous'],
                'https://example.com/media/api-cache-for-wcivf/{0}/{1}'.format(
                    expected_leafname, persons_1_leafname))
            self.assertEqual(
                posts_1_data['next'],
                'https://example.com/media/api-cache-for-wcivf/{0}/{1}'.format(
                    expected_leafname, posts_2_leafname))
            self.assertEqual(posts_1_data['previous'], None)
            self.assertEqual(posts_2_data['next'], None)
            self.assertEqual(
                posts_2_data['previous'],
                'https://example.com/media/api-cache-for-wcivf/{0}/{1}'.format(
                    expected_leafname, posts_1_leafname))
            # Check that the URL of the first person is as expected,
            # as well as it being the right person:
            first_person = persons_1_data['results'][0]
            self.assertEqual(first_person['id'], 818)
            self.assertEqual(first_person['name'], 'Sheila Gilmore')
            self.assertEqual(first_person['url'], 'https://example.com/api/v0.9/persons/818/?format=json')
            # Similarly, check that the URL of the first post is as expected:
            first_post = posts_1_data['results'][0]
            self.assertEqual(first_post['id'], self.edinburgh_east_post_extra.slug)
            self.assertEqual(first_post['label'], 'Member of Parliament for Edinburgh East')
            self.assertEqual(first_post['url'], 'https://example.com/api/v0.9/posts/14419/?format=json')
        finally:
            rmtree(target_directory)

    @patch('candidates.management.commands.candidates_cache_api_to_directory.rmtree')
    @patch('candidates.management.commands.candidates_cache_api_to_directory.datetime')
    def test_cache_api_to_directory_prune(self, mock_datetime, mock_rmtree):
        # Need to make sure datetime.strptime still works:
        mock_datetime.strptime.side_effect = datetime.strptime
        mock_datetime.now.return_value = datetime(2017, 5, 14, 12, 33, 5, 0)
        target_directory = mkdtemp()
        try:
            for d in (
                    '2017-05-12T08:00:00',
                    '2017-05-12T10:00:00',
                    '2017-05-12T12:00:00',
                    '2017-05-14T08:00:00',
                    '2017-05-14T10:00:00',
                    '2017-05-14T12:00:00',
            ):
                os.makedirs(join(target_directory, d))
            os.symlink('2017-05-12T08:00:00', join(target_directory, 'latest'))
            prune(target_directory)
            # That should have kept the last 4 + the one that latest
            # points to, so there should only have been one call to rmtree:
            self.assertEqual(mock_rmtree.call_count, 1)
            self.assertEqual(
                mock_rmtree.mock_calls[0],
                call(join(target_directory, '2017-05-12T10:00:00')))
        finally:
            rmtree(target_directory)

    @patch('candidates.management.commands.candidates_cache_api_to_directory.rmtree')
    @patch('candidates.management.commands.candidates_cache_api_to_directory.datetime')
    def test_cache_api_to_directory_prune_four_old(self, mock_datetime, mock_rmtree):
        # Need to make sure datetime.strptime still works:
        mock_datetime.strptime.side_effect = datetime.strptime
        mock_datetime.now.return_value = datetime(2017, 5, 14, 12, 33, 5, 0)
        target_directory = mkdtemp()
        try:
            for d in (
                    '2017-05-12T06:00:00',
                    '2017-05-12T08:00:00',
                    '2017-05-12T10:00:00',
                    '2017-05-12T12:00:00',
            ):
                os.makedirs(join(target_directory, d))
            prune(target_directory)
            # Even though all of those directories are more than 36
            # hours old, they should all be kept because they're the
            # most recent 4:
            self.assertEqual(mock_rmtree.call_count, 0)
        finally:
            rmtree(target_directory)

    @patch('candidates.management.commands.candidates_cache_api_to_directory.rmtree')
    @patch('candidates.management.commands.candidates_cache_api_to_directory.datetime')
    def test_cache_api_to_directory_prune_lots_very_recent(self, mock_datetime, mock_rmtree):
        # Need to make sure datetime.strptime still works:
        mock_datetime.strptime.side_effect = datetime.strptime
        mock_datetime.now.return_value = datetime(2017, 5, 14, 12, 33, 5, 0)
        target_directory = mkdtemp()
        try:
            for d in (
                    '2017-05-13T22:00:00',
                    '2017-05-14T00:00:00',
                    '2017-05-14T02:00:00',
                    '2017-05-14T04:00:00',
                    '2017-05-14T06:00:00',
                    '2017-05-14T08:00:00',
                    '2017-05-14T10:00:00',
                    '2017-05-14T12:00:00',
            ):
                os.makedirs(join(target_directory, d))
            prune(target_directory)
            # All of those are too recent to be removed, so there
            # should be no calls to rmtree:
            self.assertEqual(mock_rmtree.call_count, 0)
        finally:
            rmtree(target_directory)

    @patch('candidates.management.commands.candidates_cache_api_to_directory.rmtree')
    @patch('candidates.management.commands.candidates_cache_api_to_directory.datetime')
    def test_cache_api_prune_when_latest_is_in_last_four(self, mock_datetime, mock_rmtree):
        # Need to make sure datetime.strptime still works:
        mock_datetime.strptime.side_effect = datetime.strptime
        mock_datetime.now.return_value = datetime(2017, 5, 14, 12, 33, 5, 0)
        target_directory = mkdtemp()
        try:
            for d in (
                    '2017-05-13T22:00:00',
                    '2017-05-14T00:00:00',
                    '2017-05-14T02:00:00',
                    '2017-05-14T04:00:00',
                    '2017-05-14T06:00:00',
                    '2017-05-14T08:00:00',
                    '2017-05-14T10:00:00',
                    '2017-05-14T12:00:00',
            ):
                os.makedirs(join(target_directory, d))
            os.symlink('2017-05-14T12:00:00', join(target_directory, 'latest'))
            prune(target_directory)
            # All of those are too recent to be removed, so there
            # should be no calls to rmtree:
            self.assertEqual(mock_rmtree.call_count, 0)
        finally:
            rmtree(target_directory)

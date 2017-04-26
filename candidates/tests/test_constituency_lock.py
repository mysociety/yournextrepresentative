from __future__ import unicode_literals

from django_webtest import WebTest
from popolo.models import Person

from candidates.models import PostExtra

from .auth import TestUserMixin
from .factories import CandidacyExtraFactory, PersonExtraFactory
from .uk_examples import UK2015ExamplesMixin


def update_lock(post_extra, election, lock_status):
    postextraelection = post_extra.postextraelection_set.get(
        election=election
    )
    postextraelection.candidates_locked = lock_status
    postextraelection.save()

    return postextraelection


class TestConstituencyLockAndUnlock(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestConstituencyLockAndUnlock, self).setUp()
        update_lock(
            self.camberwell_post_extra, self.election, True
        )
        self.post_extra_id = self.dulwich_post_extra.id

    def test_constituency_lock_unauthorized(self):
        self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user,
        )
        csrftoken = self.app.cookies['csrftoken']
        response = self.app.post(
            '/election/2015/post/lock',
            {
                'lock': 'True',
                'post_id': '65808',
                'csrfmiddlewaretoken': csrftoken,
            },
            user=self.user,
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_constituency_lock_bad_submission(self):
        post_extra = PostExtra.objects.get(id=self.post_extra_id)
        update_lock(post_extra, self.election, False)
        self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user_who_can_lock,
        )
        csrftoken = self.app.cookies['csrftoken']
        with self.assertRaises(Exception) as context:
            self.app.post(
                '/election/2015/post/lock',
                {
                    'csrfmiddlewaretoken': csrftoken,
                },
                user=self.user_who_can_lock,
                expect_errors=True,
            )

            self.assertTrue('Invalid data POSTed' in context.exception)

    def test_constituency_lock(self):
        post_extra = PostExtra.objects.get(id=self.post_extra_id)
        postextraelection = update_lock(post_extra, self.election, False)
        self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user_who_can_lock,
        )
        csrftoken = self.app.cookies['csrftoken']
        response = self.app.post(
            '/election/2015/post/lock',
            {
                'lock': 'True',
                'post_id': '65808',
                'csrfmiddlewaretoken': csrftoken,
            },
            user=self.user_who_can_lock,
            expect_errors=True,
        )
        postextraelection.refresh_from_db()
        self.assertEqual(True, postextraelection.candidates_locked)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location,
            "http://localhost:80/election/2015/post/65808/dulwich-and-west-norwood"
        )

    def test_constituency_unlock(self):
        post_extra = PostExtra.objects.get(id=self.post_extra_id)
        postextraelection = update_lock(post_extra, self.election, True)
        self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user_who_can_lock,
        )
        csrftoken = self.app.cookies['csrftoken']
        response = self.app.post(
            '/election/2015/post/lock',
            {
                'lock': 'False',
                'post_id': '65808',
                'csrfmiddlewaretoken': csrftoken,
            },
            user=self.user_who_can_lock,
            expect_errors=True,
        )
        postextraelection.refresh_from_db()
        self.assertEqual(False, postextraelection.candidates_locked)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location,
            "http://localhost:80/election/2015/post/65808/dulwich-and-west-norwood"
        )

    def test_constituencies_unlocked_list(self):
        response = self.app.get(
            '/election/2015/constituencies/unlocked',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Dulwich', response.text)
        self.assertNotIn('Camberwell', response.text)


class TestConstituencyLockWorks(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestConstituencyLockWorks, self).setUp()
        update_lock(self.camberwell_post_extra, self.election, True)
        post_extra_locked = self.camberwell_post_extra
        self.post_extra_id = self.dulwich_post_extra.id
        person_extra = PersonExtraFactory.create(
            base__id='4170',
            base__name='Naomi Newstead'
        )

        CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_extra.base,
            base__post=post_extra_locked.base,
            base__on_behalf_of=self.green_party_extra.base
        )

        person_extra = PersonExtraFactory.create(
            base__id='4322',
            base__name='Helen Hayes'
        )

        CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.green_party_extra.base
        )

    def test_add_when_locked_unprivileged_disallowed(self):
        # Just get that page for the csrftoken cookie; the form won't
        # appear on the page, since the constituency is locked:
        response = self.app.get(
            '/election/2015/post/65913/camberwell-and-peckham',
            user=self.user
        )
        csrftoken = self.app.cookies['csrftoken']
        response = self.app.post(
            '/election/2015/person/create/',
            {
                'csrfmiddlewaretoken': csrftoken,
                'name': 'Imaginary Candidate',
                'party_gb_2015': self.green_party_extra.base_id,
                'constituency_2015': '65913',
                'standing_2015': 'standing',
                'source': 'Testing adding a new candidate to a locked constituency',
            },
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_add_when_locked_privileged_allowed(self):
        response = self.app.get(
            '/election/2015/post/65913/camberwell-and-peckham',
            user=self.user_who_can_lock
        )
        form = response.forms['new-candidate-form']
        form['name'] = "Imaginary Candidate"
        form['party_gb_2015'] = self.green_party_extra.base_id
        form['source'] = 'Testing adding a new candidate to a locked constituency'
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        # Find the person this should have redirected to:
        expected_person = Person.objects.get(name='Imaginary Candidate')
        self.assertEqual(
            submission_response.location,
            'http://localhost:80/person/{0}'.format(expected_person.id)
        )

    def test_move_into_locked_unprivileged_disallowed(self):
        response = self.app.get(
            '/person/4322/update',
            user=self.user
        )
        form = response.forms['person-details']
        form['source'] = 'Testing a switch to a locked constituency'
        form['constituency_2015'] = '65913'
        submission_response = form.submit(expect_errors=True)
        self.assertEqual(submission_response.status_code, 403)

    def test_move_into_locked_privileged_allowed(self):
        response = self.app.get(
            '/person/4322/update',
            user=self.user_who_can_lock
        )
        form = response.forms['person-details']
        form['source'] = 'Testing a switch to a locked constituency'
        form['constituency_2015'] = '65913'
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location,
            'http://localhost:80/person/4322'
        )

    def test_move_out_of_locked_unprivileged_disallowed(self):
        response = self.app.get(
            '/person/4170/update',
            user=self.user
        )
        form = response.forms['person-details']
        form['source'] = 'Testing a switch to a unlocked constituency'
        form['constituency_2015'] = '65808'
        submission_response = form.submit(expect_errors=True)
        self.assertEqual(submission_response.status_code, 403)

    def test_move_out_of_locked_privileged_allowed(self):
        response = self.app.get(
            '/person/4170/update',
            user=self.user_who_can_lock
        )
        form = response.forms['person-details']
        form['source'] = 'Testing a switch to a unlocked constituency'
        form['constituency_2015'] = '65808'
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location,
            'http://localhost:80/person/4170'
        )

    # Now the tests to check that the only privileged users can change
    # the parties of people in locked constituecies.

    def test_change_party_in_locked_unprivileged_disallowed(self):
        response = self.app.get(
            '/person/4170/update',
            user=self.user
        )
        form = response.forms['person-details']
        form['source'] = 'Testing a party change in a locked constituency'
        form['party_gb_2015'] = self.conservative_party_extra.base_id
        submission_response = form.submit(expect_errors=True)
        self.assertEqual(submission_response.status_code, 403)

    def test_change_party_in_locked_privileged_allowed(self):
        response = self.app.get(
            '/person/4170/update',
            user=self.user_who_can_lock
        )
        form = response.forms['person-details']
        form['source'] = 'Testing a party change in a locked constituency'
        form['party_gb_2015'] = self.conservative_party_extra.base_id
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location,
            'http://localhost:80/person/4170'
        )

    def test_change_party_in_unlocked_unprivileged_allowed(self):
        response = self.app.get(
            '/person/4322/update',
            user=self.user
        )
        form = response.forms['person-details']
        form['source'] = 'Testing a party change in an unlocked constituency'
        form['party_gb_2015'] = self.conservative_party_extra.base_id
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location,
            'http://localhost:80/person/4322'
        )

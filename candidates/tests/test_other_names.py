from __future__ import print_function, unicode_literals

from django_webtest import WebTest

from popolo.models import OtherName

from .auth import TestUserMixin
from .factories import PersonExtraFactory
from .uk_examples import UK2015ExamplesMixin


class TestOtherNamesViews(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestOtherNamesViews, self).setUp()
        self.pe_no_other = PersonExtraFactory.create(
            base__id=1234,
            base__name='John Smith',
        )
        self.pe_other_names = PersonExtraFactory.create(
            base__id=5678,
            base__name='Fozzie',
        )
        self.fozziewig = OtherName.objects.create(
            content_object=self.pe_other_names.base,
            name='Mr Fozziewig',
            note='In a Muppet Christmas Carol',
        )
        self.fozzie_bear = OtherName.objects.create(
            content_object=self.pe_other_names.base,
            name='Fozzie Bear',
            note='Full name',
        )

    # Listing

    def test_list_other_names_no_names(self):
        response = self.app.get('/person/1234/other-names')
        self.assertIn(
            'No alternative names found',
            response.text
        )

    def test_list_other_names_some_Names(self):
        response = self.app.get('/person/5678/other-names')
        self.assertIn(
            '<strong>Name</strong>: Fozzie Bear',
            response.text
        )
        self.assertIn(
            '<strong>Name</strong>: Mr Fozziewig',
            response.text
        )

    # Deleting

    def test_delete_other_name_not_authenticated(self):
        # Get the page so we'll have a CSRF token:
        response = self.app.get('/person/5678/other-names')
        url = '/person/5678/other-name/{on_id}/delete'.format(
            on_id=self.fozzie_bear.id,
        )
        response = self.app.post(
            url,
            {
                'csrfmiddlewaretoken': self.app.cookies['csrftoken'],
                'source': 'Some good reasons for deleting this name',
            },
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_delete_other_name_authenticated_works(self):
        # Get the page so we'll have a CSRF token:
        response = self.app.get('/person/5678/other-names')
        url = '/person/5678/other-name/{on_id}/delete'.format(
            on_id=self.fozzie_bear.id,
        )
        response = self.app.post(
            url,
            {
                'csrfmiddlewaretoken': self.app.cookies['csrftoken'],
                'source': 'Some good reasons for deleting this name',
            },
            user=self.user,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location,
            'http://localhost:80/person/5678/other-names'
        )
        self.assertEqual(
            1,
            self.pe_other_names.base.other_names.count(),
        )
        self.assertEqual(
            self.pe_other_names.base.other_names.get().name,
            'Mr Fozziewig',
        )

    # Adding

    def test_add_other_name_get_not_authenticated(self):
        # Get the create page:
        response = self.app.get(
            '/person/5678/other-names/create',
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_add_other_name_post_not_authenticated(self):
        # Get a page we can view to get the CSRF token:
        response = self.app.get('/person/5678/other-names')
        # Post to the create page:
        response = self.app.post(
            '/person/5678/other-names/create',
            {
                'name': 'J Smith',
                'note': 'Name with just initials',
                'csrfmiddlewaretoken': self.app.cookies['csrftoken'],
            },
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_add_other_name_authenticated_no_source(self):
        # Get a page we can view to get the CSRF token:
        response = self.app.get(
            '/person/5678/other-names/create',
            user=self.user,
        )
        form = response.forms['person_create_other_name']
        form['name'] = 'J Smith'
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 200)
        self.assertIn(
            'You forgot to reference a source',
            submission_response.text
        )

    def test_add_other_name_authenticated_succeeds(self):
        # Get a page we can view to get the CSRF token:
        response = self.app.get(
            '/person/5678/other-names/create',
            user=self.user,
        )
        form = response.forms['person_create_other_name']
        form['name'] = 'F Bear'
        form['source'] = 'Some reasonable explanation'
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location,
            'http://localhost:80/person/5678/other-names'
        )
        self.assertEqual(
            3,
            self.pe_other_names.base.other_names.count(),
        )

    # Editing

    def test_edit_other_name_get_not_authenticated(self):
        # Get the edit page:
        response = self.app.get(
            '/person/5678/other-name/{on_id}/update'.format(
                on_id=self.fozzie_bear.id,
            ),
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_edit_other_name_post_not_authenticated(self):
        # Get a page we can view to get the CSRF token:
        response = self.app.get('/person/5678/other-names')
        # Post to the edit page:
        response = self.app.post(
            '/person/5678/other-name/{on_id}/update'.format(
                on_id=self.fozzie_bear.id,
            ),
            {
                'name': 'F Bear',
                'note': 'Name with just initials',
                'csrfmiddlewaretoken': self.app.cookies['csrftoken'],
            },
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_edit_other_name_authenticated_no_source(self):
        # Get a page we can view to get the CSRF token:
        response = self.app.get(
            '/person/5678/other-name/{on_id}/update'.format(
                on_id=self.fozzie_bear.id,
            ),
            user=self.user,
        )
        form = response.forms['person_update_other_name']
        form['name'] = 'F Bear'
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 200)
        self.assertIn(
            'You forgot to reference a source',
            submission_response.text
        )

    def test_edit_other_name_authenticated_succeeds(self):
        # Get a page we can view to get the CSRF token:
        response = self.app.get(
            '/person/5678/other-name/{on_id}/update'.format(
                on_id=self.fozzie_bear.id,
            ),
            user=self.user,
        )
        form = response.forms['person_update_other_name']
        form['name'] = 'F Bear'
        form['source'] = 'Some reasonable explanation'
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location,
            'http://localhost:80/person/5678/other-names'
        )
        self.assertEqual(
            2,
            self.pe_other_names.base.other_names.count(),
        )

from __future__ import unicode_literals

from django.utils.six.moves.urllib_parse import urlsplit

from django_webtest import WebTest

from .auth import TestUserMixin
from .uk_examples import UK2015ExamplesMixin


class TestCopyrightAssignment(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestCopyrightAssignment, self).setUp()

    def test_new_person_submission_refused_copyright(self):
        response = self.app.get(
            '/constituency/65808/dulwich-and-west-norwood',
            user=self.user_refused,
        )
        split_location = urlsplit(response.location)
        self.assertEqual(
            '/copyright-question',
            split_location.path
        )
        self.assertEqual(
            'next=/constituency/65808/dulwich-and-west-norwood',
            split_location.query
        )

    def test_copyright_assigned(self):
        response = self.app.get(
            '/constituency/65808/dulwich-and-west-norwood',
            user=self.user_refused,
            auto_follow=True
        )

        form = response.forms['copyright_assignment']
        form['assigned_to_dc'] = True
        form_response = form.submit()

        split_location = urlsplit(form_response.location)
        self.assertEqual(
            '/constituency/65808/dulwich-and-west-norwood',
            split_location.path
        )

        agreement = self.user_refused.terms_agreement
        agreement.refresh_from_db()
        self.assertTrue(agreement.assigned_to_dc)

    def test_copyright_assignment_refused(self):
        response = self.app.get(
            '/constituency/65808/dulwich-and-west-norwood',
            user=self.user_refused,
            auto_follow=True
        )

        response.mustcontain(no='You can only edit data on example.com')

        form = response.forms['copyright_assignment']
        form['assigned_to_dc'] = False
        form_response = form.submit()

        form_response.mustcontain('You can only edit data on example.com')

        agreement = self.user_refused.terms_agreement
        agreement.refresh_from_db()
        self.assertFalse(agreement.assigned_to_dc)

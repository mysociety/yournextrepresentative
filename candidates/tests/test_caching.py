from __future__ import unicode_literals

from django_webtest import WebTest

from .auth import TestUserMixin
from .uk_examples import UK2015ExamplesMixin


class TestCaching(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestCaching, self).setUp()

    def test_unauth_user_cache_headers(self):
        response = self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
        )

        headers = response.headerlist
        seen_cache = False
        for header, value in headers:
            if header == 'Cache-Control':
                seen_cache = True
                self.assertTrue(value == 'max-age=1200')

        self.assertTrue(seen_cache)

    def test_auth_user_cache_headers(self):
        response = self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user
        )

        headers = response.headerlist
        seen_cache = False
        for header, value in headers:
            if header == 'Cache-Control':
                seen_cache = True
                self.assertTrue(
                    value == 'no-cache, no-store, must-revalidate, max-age=0'
                )

        self.assertTrue(seen_cache)

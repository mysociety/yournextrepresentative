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
                values = set(value.split(', '))
                self.assertEqual(
                    values,
                    {'no-cache', 'no-store', 'must-revalidate', 'max-age=0'}
                )

        self.assertTrue(seen_cache)

    def test_api_post_endpoint(self):
        # This is a regression test for the error:
        # Internal Server Error: /api/v0.9/posts/WMC:E14001021
        # Traceback (most recent call last):
        #   File "/var/www/ynr/env/local/lib/python2.7/site-packages/django/core/handlers/base.py", line 223, in get_response
        #     response = middleware_method(request, response)
        #   File "/var/www/ynr/code/candidates/middleware.py", line 97, in process_response
        #     if request.user.is_authenticated():
        # AttributeError: 'WSGIRequest' object has no attribute 'user'
        without_slash = '/api/v0.9/posts/{0}'.format(
            self.edinburgh_east_post_extra.slug)
        with_slash = without_slash + '/'
        response = self.app.get(without_slash)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.location, 'http://localhost:80' + with_slash)
        response = self.app.get(with_slash)
        self.assertEqual(response.status_code, 200)

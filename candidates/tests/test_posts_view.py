from __future__ import unicode_literals

from django_webtest import WebTest

from .uk_examples import UK2015ExamplesMixin


class TestPostsView(UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestPostsView, self).setUp()

    def test_single_election_posts_page(self):

        response = self.app.get('/posts')

        self.assertTrue(
            response.html.find(
                'h2', text='2015 General Election'
            )
        )

        self.assertTrue(
            response.html.find(
                'a', text='Member of Parliament for Camberwell and Peckham'
            )
        )

    def test_two_elections_posts_page(self):

        self.earlier_election.current = True
        self.earlier_election.save()

        response = self.app.get('/posts')

        self.assertTrue(
            response.html.find(
                'h2', text='2010 General Election'
            )
        )

        self.assertTrue(
            response.html.find(
                'h2', text='2015 General Election'
            )
        )

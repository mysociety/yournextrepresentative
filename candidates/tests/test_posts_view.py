from __future__ import unicode_literals

from django_webtest import WebTest

from .uk_examples import UK2015ExamplesMixin


class TestPostsView(UK2015ExamplesMixin, WebTest):

    def test_single_election_posts_page(self):

        response = self.app.get('/posts')

        self.assertTrue(
            response.html.find(
                'h4', text='2015 General Election'
            )
        )

        self.assertTrue(
            response.html.find(
                'a', text='Member of Parliament for Camberwell and Peckham'
            )
        )

    def test_elections_link_to_constituencies_page(self):

        response = self.app.get('/posts')

        heading = response.html.find('h4', text='2015 General Election')
        heading_children = list(heading.children)
        self.assertEqual(len(heading_children), 1)
        expected_link_element = heading_children[0]
        self.assertEqual(expected_link_element.name, 'a')
        self.assertEqual(expected_link_element['href'], '/election/2015/constituencies')
        self.assertEqual(expected_link_element.text, '2015 General Election')

    def test_two_elections_posts_page(self):

        self.earlier_election.current = True
        self.earlier_election.save()

        response = self.app.get('/posts')

        self.assertTrue(
            response.html.find(
                'h4', text='2010 General Election'
            )
        )

        self.assertTrue(
            response.html.find(
                'h4', text='2015 General Election'
            )
        )

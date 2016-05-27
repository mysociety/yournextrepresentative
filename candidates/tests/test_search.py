import re

from django.core.management import call_command
from django_webtest import WebTest

from .auth import TestUserMixin
from .settings import SettingsMixin

from popolo.models import Person

from .uk_examples import UK2015ExamplesMixin

class TestSearchView(TestUserMixin, SettingsMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestSearchView, self).setUp()
        call_command('rebuild_index', verbosity=0, interactive=False)

    def test_search_page(self):
        # we have to create the candidate by submitting the form as otherwise
        # we're not making sure the index update hook fires
        response = self.app.get('/search?q=Elizabeth')
        # have to use re to avoid matching search box
        self.assertFalse(
            re.search(
                r'''<a[^>]*>Elizabeth''',
                response.text
            )
        )

        self.assertFalse(
            re.search(
                r'''<a[^>]*>Mr Darcy''',
                response.text
            )
        )

        response = self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user,
        )
        form = response.forms['new-candidate-form']
        form['name'] = 'Mr Darcy'
        form['email'] = 'darcy@example.com'
        form['source'] = 'Testing adding a new person to a post'
        form['party_gb_2015'] = self.labour_party_extra.base_id
        form.submit()

        response = self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user,
        )
        form = response.forms['new-candidate-form']
        form['name'] = 'Elizabeth Bennet'
        form['email'] = 'lizzie@example.com'
        form['source'] = 'Testing adding a new person to a post'
        form['party_gb_2015'] = self.labour_party_extra.base_id
        form.submit()

        response = self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user,
        )
        form = response.forms['new-candidate-form']
        form['name'] = "Charlotte O'Lucas" # testers license
        form['email'] = 'charlotte@example.com'
        form['source'] = 'Testing adding a new person to a post'
        form['party_gb_2015'] = self.labour_party_extra.base_id
        form.submit()

        # check searching finds them
        response = self.app.get('/search?q=Elizabeth')
        self.assertTrue(
            re.search(
                r'''<a[^>]*>Elizabeth''',
                response.text
            )
        )

        self.assertFalse(
            re.search(
                r'''<a[^>]*>Mr Darcy''',
                response.text
            )
        )

        response = self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user,
        )
        form = response.forms['new-candidate-form']
        form['name'] = 'Elizabeth Jones'
        form['email'] = 'e.jones@example.com'
        form['source'] = 'Testing adding a new person to a post'
        form['party_gb_2015'] = self.labour_party_extra.base_id
        form.submit()

        response = self.app.get('/search?q=Elizabeth')
        self.assertTrue(
            re.search(
                r'''<a[^>]*>Elizabeth Bennet''',
                response.text
            )
        )
        self.assertTrue(
            re.search(
                r'''<a[^>]*>Elizabeth Jones''',
                response.text
            )
        )

        person = Person.objects.get(name='Elizabeth Jones')
        response = self.app.get(
            '/person/{0}/update'.format(person.id),
            user=self.user,
        )
        form = response.forms['person-details']
        form['name'] = 'Lizzie Jones'
        form['source'] = "Some source of this information"
        form.submit()

        response = self.app.get('/search?q=Elizabeth')
        self.assertTrue(
            re.search(
                r'''<a[^>]*>Elizabeth Bennet''',
                response.text
            )
        )
        self.assertFalse(
            re.search(
                r'''<a[^>]*>Elizabeth Jones''',
                response.text
            )
        )

        # check that searching for names with apostrophe works
        response = self.app.get("/search?q=O'Lucas")
        self.assertTrue(
            re.search(
                r'''<a[^>]*>Charlotte''',
                response.text
            )
        )

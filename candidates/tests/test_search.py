import re

from django.core.management import call_command
from django_webtest import WebTest

from .auth import TestUserMixin

from popolo.models import Person

from .factories import (
    AreaTypeFactory, ElectionFactory, PostExtraFactory,
    ParliamentaryChamberFactory, PartyFactory, PartyExtraFactory,
    PartySetFactory
)


class TestSearchView(TestUserMixin, WebTest):

    def setUp(self):
        wmc_area_type = AreaTypeFactory.create()
        gb_parties = PartySetFactory.create(slug='gb', name='Great Britain')
        election = ElectionFactory.create(
            slug='2015',
            name='2015 General Election',
            area_types=(wmc_area_type,)
        )
        commons = ParliamentaryChamberFactory.create()
        post_extra = PostExtraFactory.create(
            elections=(election,),
            base__organization=commons,
            slug='65808',
            party_set=gb_parties,
            base__label='Member of Parliament for Dulwich and West Norwood'
        )
        PartyExtraFactory.reset_sequence()
        PartyFactory.reset_sequence()
        self.parties = {}
        for i in range(0, 4):
            party_extra = PartyExtraFactory.create()
            gb_parties.parties.add(party_extra.base)
            self.parties[party_extra.slug] = party_extra

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
        form['party_gb_2015'] = self.parties['party:53'].base_id
        submission_response = form.submit()

        response = self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user,
        )
        form = response.forms['new-candidate-form']
        form['name'] = 'Elizabeth Bennet'
        form['email'] = 'lizzie@example.com'
        form['source'] = 'Testing adding a new person to a post'
        form['party_gb_2015'] = self.parties['party:53'].base_id
        submission_response = form.submit()

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
        form['party_gb_2015'] = self.parties['party:53'].base_id
        submission_response = form.submit()

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
        submission_response = form.submit()

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

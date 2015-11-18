from urlparse import urlsplit

from django_webtest import WebTest

from .auth import TestUserMixin

from popolo.models import Person

from .factories import (
    AreaTypeFactory, ElectionFactory, CandidacyExtraFactory,
    ParliamentaryChamberFactory, PartyFactory, PartyExtraFactory,
    PersonExtraFactory, PostExtraFactory
)


class TestUpdatePersonView(TestUserMixin, WebTest):

    """
    this has to be a class method as the static_data stuff
    is only created once and if we recreate the parties etc
    every time then they end up with different IDs in the
    form than the PARTY_DATA etc and things break
    """
    @classmethod
    def setUpClass(cls):
        super(TestUpdatePersonView, cls).setUpClass()
        wmc_area_type = AreaTypeFactory.create()
        cls.election = ElectionFactory.create(
            slug='2015',
            name='2015 General Election',
            area_types=(wmc_area_type,)
        )
        commons = ParliamentaryChamberFactory.create()
        cls.post_extra = PostExtraFactory.create(
            elections=(cls.election,),
            base__organization=commons,
            slug='65808',
            base__label='Member of Parliament for Dulwich and West Norwood'
        )
        PartyExtraFactory.reset_sequence()
        PartyFactory.reset_sequence()
        cls.parties = {}
        for i in xrange(0, 4):
            party_extra = PartyExtraFactory.create()
            cls.parties[party_extra.slug] = party_extra

    def setUp(self):
        person_extra = PersonExtraFactory.create(
            base__id='2009',
            base__name='Tessa Jowell'
        )

        CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_extra.base,
            base__post=self.post_extra.base,
            base__on_behalf_of=self.parties['party:63'].base
        )

    def test_update_person_view_get_without_login(self):
        response = self.app.get('/person/2009/update')
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual('/accounts/login/', split_location.path)
        self.assertEqual('next=/person/2009/update', split_location.query)

    def test_update_person_view_get_refused_copyright(self):
        response = self.app.get('/person/2009/update', user=self.user_refused)
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual('/copyright-question', split_location.path)
        self.assertEqual('next=/person/2009/update', split_location.query)

    def test_update_person_view_get(self):
        # For the moment just check that the form's actually there:
        response = self.app.get('/person/2009/update', user=self.user)
        form = response.forms['person-details']
        self.assertIsNotNone(form)

    def test_update_person_submission_copyright_refused(self):
        response = self.app.get('/person/2009/update', user=self.user)
        form = response.forms['person-details']
        form['wikipedia_url'] = 'http://en.wikipedia.org/wiki/Tessa_Jowell'
        form['party_national_2015'] = self.parties['party:53'].base_id
        form['source'] = "Some source of this information"
        submission_response = form.submit(user=self.user_refused)
        split_location = urlsplit(submission_response.location)
        self.assertEqual('/copyright-question', split_location.path)
        self.assertEqual('next=/person/2009/update', split_location.query)

    def test_update_person_submission(self):
        response = self.app.get(
            '/person/2009/update',
            user=self.user_who_can_lock,
        )
        form = response.forms['person-details']
        form['wikipedia_url'] = 'http://en.wikipedia.org/wiki/Tessa_Jowell'
        form['party_national_2015'] = self.parties['party:53'].base_id
        form['source'] = "Some source of this information"
        submission_response = form.submit()

        person = Person.objects.get(id='2009')
        party = person.memberships.filter(role='Candidate')

        self.assertEqual(party.count(), 1)
        self.assertEqual(party[0].on_behalf_of.extra.slug, 'party:53')

        links = person.links.all()
        self.assertEqual(links.count(), 1)
        self.assertEqual(links[0].url, 'http://en.wikipedia.org/wiki/Tessa_Jowell')

        # It should redirect back to the same person's page:
        split_location = urlsplit(submission_response.location)
        self.assertEqual(
            '/person/2009',
            split_location.path
        )

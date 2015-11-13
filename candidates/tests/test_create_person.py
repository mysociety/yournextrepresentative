from django_webtest import WebTest

from .auth import TestUserMixin

from popolo.models import Person

from .factories import (
    AreaTypeFactory, ElectionFactory, ParliamentaryChamberFactory,
    PartyFactory, PartyExtraFactory, PostExtraFactory
)


class TestCreatePerson(TestUserMixin, WebTest):

    def setUp(self):
        wmc_area_type = AreaTypeFactory.create()
        election = ElectionFactory.create(
            slug='2015',
            name='2015 General Election',
            area_types=(wmc_area_type,)
        )
        commons = ParliamentaryChamberFactory.create()
        PostExtraFactory.create(
            elections=(election,),
            base__organization=commons,
            base__id='65808',
            base__label='Member of Parliament for Dulwich and West Norwood'
        )
        PartyFactory.reset_sequence()
        parties = {}
        for i in xrange(0, 4):
            party_extra = PartyExtraFactory.create()
            parties[party_extra.base.id] = party_extra

    def test_create_from_post_page(self):
        response = self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user,
        )
        form = response.forms['new-candidate-form']
        form['name'] = 'Elizabeth Bennet'
        form['email'] = 'lizzie@example.com'
        form['source'] = 'Testing adding a new person to a post'
        form['party_national_2015'] = 'party:53'
        submission_response = form.submit()
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location,
            'http://localhost:80/person/1'
        )

        person = Person.objects.get(id=1)
        self.assertEqual(person.name, 'Elizabeth Bennet')
        self.assertEqual(person.memberships.count(), 1)

        candidacy = person.memberships.first()

        self.assertEqual(candidacy.post_id, '65808')
        self.assertEqual(candidacy.role, 'Candidate')
        self.assertEqual(candidacy.on_behalf_of_id, 'party:53')
        self.assertEqual(candidacy.extra.election_id, 1)

import json
from urlparse import urlsplit

from django_webtest import WebTest

from popolo.models import Person

from .auth import TestUserMixin
from ..models import LoggedAction

from .factories import (
    AreaTypeFactory, ElectionFactory, ParliamentaryChamberFactory,
    PartyFactory, PartyExtraFactory, PostExtraFactory,
    ParliamentaryChamberExtraFactory
)


class TestNewPersonView(TestUserMixin, WebTest):

    """
    this has to be a class method as the static_data stuff
    is only created once and if we recreate the parties etc
    every time then they end up with different IDs in the
    form than the PARTY_DATA etc and things break
    """
    @classmethod
    def setUpClass(cls):
        super(TestNewPersonView, cls).setUpClass()
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

    def test_new_person_submission_refused_copyright(self):
        # Just a smoke test for the moment:
        response = self.app.get(
            '/constituency/65808/dulwich-and-west-norwood',
            user=self.user_refused
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

    def test_new_person_submission(self):
        response = self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user,
        )
        form = response.forms['new-candidate-form']
        form['name'] = 'Elizabeth Bennet'
        form['email'] = 'lizzie@example.com'
        form['party_national_2015'] = self.parties['party:53'].base_id
        form['wikipedia_url'] = 'http://en.wikipedia.org/wiki/Lizzie_Bennet'
        submission_response = form.submit()

        # If there's no source specified, it shouldn't ever get to
        # update_person, and redirect back to the constituency page:
        self.assertEqual(submission_response.status_code, 200)

        self.assertContains(
            submission_response,
            'You must indicate how you know about this candidate'
        )

        form['source'] = 'Testing adding a new person to a post'
        submission_response = form.submit()

        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location,
            'http://localhost:80/person/1'
        )

        person = Person.objects.get(id=1)
        self.assertEqual(person.name, 'Elizabeth Bennet')
        self.assertEqual(person.email, 'lizzie@example.com')

        self.assertEqual(person.memberships.count(), 1)

        candidacy = person.memberships.first()

        self.assertEqual(candidacy.post.extra.slug, '65808')
        self.assertEqual(candidacy.role, 'Candidate')
        self.assertEqual(candidacy.on_behalf_of.extra.slug, 'party:53')
        self.assertEqual(candidacy.extra.election_id, 1)

        links = person.links.all()
        self.assertEqual(links.count(), 1)
        self.assertEqual(links[0].url, 'http://en.wikipedia.org/wiki/Lizzie_Bennet')

        self.assertNotEqual(person.extra.versions, '[]')

        versions = json.loads(person.extra.versions)
        self.assertEqual(len(versions), 1)
        self.assertEqual(versions[0]['information_source'],
                         'Testing adding a new person to a post')

        last_logged_action = LoggedAction.objects.all().order_by('-created')[0]
        self.assertEqual(
            last_logged_action.person_id,
            1,
        )
        self.assertEqual(
            last_logged_action.action_type,
            'person-create'
        )

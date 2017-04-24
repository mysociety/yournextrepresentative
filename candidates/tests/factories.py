from __future__ import unicode_literals

from datetime import date, timedelta

import factory

from .dates import date_in_near_future, FOUR_YEARS_IN_DAYS


class AreaTypeFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'elections.AreaType'

    name = 'WMC'
    source = 'MapIt'


class PartySetFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'candidates.PartySet'


class ParliamentaryChamberFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'popolo.Organization'

    name = 'House of Commons'


class ParliamentaryChamberExtraFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'candidates.OrganizationExtra'

    slug = 'commons'
    base = factory.SubFactory(ParliamentaryChamberFactory)


class BaseElectionFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'elections.Election'
        abstract = True

    slug = 'sp.2016-05-05'
    for_post_role = 'Member of the Scottish Parliament'
    winner_membership_role = None
    candidate_membership_role = 'Candidate'
    election_date = date_in_near_future
    name = 'Scottish Parliamentary elections'
    current = True
    use_for_candidate_suggestions = False
    area_generation = 22
    party_lists_in_use = False
    default_party_list_members_to_show = 0
    show_official_documents = True
    ocd_division = ''
    description = ''


class ElectionFactory(BaseElectionFactory):

    class Meta:
        model = 'elections.Election'

    # FIXME: not sure why this can't be in the base class
    @factory.post_generation
    def area_types(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for area_type in extracted:
                self.area_types.add(area_type)


class EarlierElectionFactory(BaseElectionFactory):

    class Meta:
        model = 'elections.Election'

    slug = 'earlier-general-election'
    name = 'Earlier General Election'
    election_date = \
        date_in_near_future - timedelta(days=FOUR_YEARS_IN_DAYS)
    current = False
    use_for_candidate_suggestions = True

    # FIXME: not sure why this can't be in the base class
    @factory.post_generation
    def area_types(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for area_type in extracted:
                self.area_types.add(area_type)


class AreaFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'popolo.Area'


class AreaExtraFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'candidates.AreaExtra'

    base = factory.SubFactory(AreaFactory)


class PostFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'popolo.Post'

    role = 'Member of Parliament'


class PostExtraElectionFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'candidates.PostExtraElection'


class PostExtraFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'candidates.PostExtra'

    base = factory.SubFactory(PostFactory)

    @factory.post_generation
    def elections(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for election in extracted:
                PostExtraElectionFactory.create(
                    postextra=self,
                    election=election
                )


class OrganizationFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'popolo.Organization'


class OrganizationExtraFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'candidates.OrganizationExtra'
    base = factory.SubFactory(OrganizationFactory)


class PartyFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'popolo.Organization'

    classification='Party'
    end_date = "9999-12-31"


class PartyExtraFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'candidates.OrganizationExtra'

    register = 'Great Britain'

    base = factory.SubFactory(PartyFactory)


class PersonFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'popolo.Person'


class PersonExtraFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'candidates.PersonExtra'

    base = factory.SubFactory(PersonFactory)
    versions = '[]'


class MembershipFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'popolo.Membership'


class MembershipExtraFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'candidates.MembershipExtra'

    base = factory.SubFactory(MembershipFactory)


class CandidacyFactory(MembershipFactory):

    role = 'Candidate'


class CandidacyExtraFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'candidates.MembershipExtra'

    base = factory.SubFactory(CandidacyFactory)

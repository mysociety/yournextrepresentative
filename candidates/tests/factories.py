from datetime import date, timedelta

import factory

date_in_near_future = date.today() + timedelta(days=14)

FOUR_YEARS_IN_DAYS = 1462


class AreaTypeFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'elections.AreaType'

    name = 'WMC'
    source = 'MapIt'


class ParliamentaryChamberFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'popolo.Organization'

    id = 'commons'
    name = 'House of Commons'


class BaseElectionFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'elections.Election'
        abstract = True

    slug = 'general-election'
    for_post_role = 'Member of Parliament'
    winner_membership_role = None
    candidate_membership_role = 'Candidate'
    election_date = date_in_near_future
    candidacy_start_date = \
        date_in_near_future - timedelta(days=(FOUR_YEARS_IN_DAYS - 1))
    name = 'General Election'
    current = True
    use_for_candidate_suggestions = False
    party_membership_start_date = \
        date_in_near_future - timedelta(days=(FOUR_YEARS_IN_DAYS - 1))
    party_membership_end_date = date(9999, 12, 31)
    area_generation = 22
    post_id_format = '{area_id}'
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


class EarlierElectionFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'elections.Election'

    slug = 'earlier-general-election'
    name = 'Earlier General Election'
    election_date = \
        date_in_near_future - timedelta(days=FOUR_YEARS_IN_DAYS)
    candidacy_start_date = \
        date_in_near_future - timedelta(days=(FOUR_YEARS_IN_DAYS*2))
    party_membership_start_date = \
        date_in_near_future - timedelta(days=(FOUR_YEARS_IN_DAYS*2))
    party_membership_end_date = \
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


EXAMPLE_CONSTITUENCIES = [
    {'id': '14419', 'name': 'Edinburgh East'},
    {'id': '14420', 'name': 'Edinburgh North and Leith'},
    {'id': '65808', 'name': 'Dulwich and West Norwood'},
    {'id': '65913', 'name': 'Camberwell and Peckham'},
]

def get_constituency_id(n):
    if n < len(EXAMPLE_CONSTITUENCIES):
        return EXAMPLE_CONSTITUENCIES[n]['id']
    else:
        return str(70000 + n)

def get_post_label(n):
    if n < len(EXAMPLE_CONSTITUENCIES):
        constituency_name = EXAMPLE_CONSTITUENCIES[n]['name']
    else:
        constituency_name = 'Constituency {n}'.format(n=n)
    return 'Member of Parliament for {constituency_name}'.format(
        constituency_name=constituency_name
    )


class PostFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'popolo.Post'

    id = factory.Sequence(get_constituency_id)
    label = factory.Sequence(get_post_label)
    role = 'Member of Parliament'


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
                self.elections.add(election)


EXAMPLE_PARTIES = [
    {'id': 'party:53', 'name': 'Labour Party'},
    {'id': 'party:90', 'name': 'Liberal Democrats'},
    {'id': 'party:63', 'name': 'Green Party'},
    {'id': 'party:52', 'name': 'Conservative Party'},
]

def get_party_id(n):
    if n < len(EXAMPLE_PARTIES):
        return EXAMPLE_PARTIES[n]['id']
    else:
        return 'party:{ec_id}'.format(ec_id=(10000 + n))

def get_party_name(n):
    if n < len(EXAMPLE_PARTIES):
        party_name = EXAMPLE_PARTIES[n]['name']
    else:
        party_name = 'Party {n}'.format(n=n)
    return party_name


class PartyFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'popolo.Organization'

    id = factory.Sequence(get_party_id)
    name = factory.Sequence(get_party_name)
    classification='Party'


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


class MembershipFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'popolo.Membership'

    id = factory.Sequence(lambda n: n)


class CandidacyFactory(MembershipFactory):

    role = 'Candidate'


class CandidacyExtraFactory(factory.DjangoModelFactory):

    class Meta:
        model = 'candidates.MembershipExtra'

    base = factory.SubFactory(CandidacyFactory)

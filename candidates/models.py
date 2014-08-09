from django.db import models

# Create your models here.

class PopItPerson(object):

    def __init__(self, api=None, popit_data=None):
        self.popit_data = popit_data
        self.api = api

    @classmethod
    def create_from_popit(cls, api, popit_person_id):
        popit_data = api.persons(popit_person_id).get()['result']
        return cls(api=api, popit_data=popit_data)

    @property
    def name(self):
        return self.popit_data['name']

    def get_party(self):
        for m in self.popit_data['memberships']:
            # FIXME: note that this fetches a huge object from the
            # API, since the organisation object for a party has a
            # list of all its memberships inline, which can be
            # hundreds of people for a major party. See the comment on
            # the related issue here:
            # https://github.com/mysociety/popit/issues/593#issuecomment-51690405
            o = self.api.organizations(m['organization_id']).get()['result']
            # FIXME: this is just quick and broken implementation -
            # it's obviously not correct, because if someone changes
            # parties between the 2010 and 2015 elections, they'll
            # have multiple party memberships, and this will pick one
            # at random.  However, at the moment there's no date
            # information for party memberships either, so let's deal
            # with that later.
            if o['classification'] == 'Party':
                return o
        return None

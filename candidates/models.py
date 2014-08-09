from django.db import models

# Create your models here.

class PopItPerson(object):

    def __init__(self, popit_data=None):
        self.popit_data = popit_data

    @classmethod
    def create_from_popit(cls, api, popit_person_id):
        popit_data = api.persons(popit_person_id).get()['result']
        return cls(popit_data)

    @property
    def name(self):
        return self.popit_data['name']

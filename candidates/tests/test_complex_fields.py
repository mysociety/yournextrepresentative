# -*- coding: utf-8 -*-

import re
from django.utils.six.moves.urllib_parse import urlsplit

from django_webtest import WebTest
from popolo.models import Person

from candidates.models import PersonExtra, ComplexPopoloField

from .auth import TestUserMixin
from .uk_examples import UK2015ExamplesMixin


def get_next_dd(start):
    return [t for t in start.next_siblings if t.name == 'dd'][0]


class ComplexFieldsTests(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(ComplexFieldsTests, self).setUp()

        an_field = ComplexPopoloField.objects.create(
            name='additional_link',
            label='Additional Link',
            popolo_array='links',
            field_type='url',
            info_type_key='note',
            info_type='additional_link',
            info_value_key='url',
            order=0,
        )

        # Create one person with these fields already present:
        self.person = Person.objects.create(
            name="John the Well-Described",
        )
        self.person_extra = PersonExtra.objects.create(base=self.person, versions='[]')
        self.person_extra.update_complex_field(an_field, 'http://example.com/additional')

    def test_create_form_has_fields(self):
        response = self.app.get(
            '/election/2015/person/create/',
            user=self.user
        )
        self.assertEqual(response.status_code, 200)
        an_label = response.html.find('label', {'for': 'id_additional_link'})
        self.assertIsNotNone(an_label)
        an_input = response.html.find('input', {'id': 'id_additional_link'})
        self.assertIsNotNone(an_input)

    def test_update_form_is_prefilled(self):
        response = self.app.get(
            '/person/{person_id}/update'.format(person_id=self.person.id),
            user=self.user,
        )
        an_label = response.html.find('label', {'for': 'id_additional_link'})
        self.assertIsNotNone(an_label)
        an_input = response.html.find('input', {'id': 'id_additional_link'})
        self.assertIsNotNone(an_input)
        self.assertEqual(an_input.get('value'), 'http://example.com/additional')

    def test_fields_are_saved_when_editing(self):
        response = self.app.get(
            '/person/{person_id}/update'.format(person_id=self.person.id),
            user=self.user,
        )
        form = response.forms['person-details']
        form['additional_link'] = 'http://example.com/anotherlink'
        form['source'] = 'Testing setting complex fields'
        submission_response = form.submit()

        self.assertEqual(submission_response.status_code, 302)
        split_location = urlsplit(submission_response.location)
        self.assertEqual(
            '/person/{person_id}'.format(person_id=self.person.id),
            split_location.path
        )

        person = Person.objects.get(id=self.person.id)
        self.assertEqual(person.extra.additional_link, 'http://example.com/anotherlink')

    def test_fields_are_saved_when_creating(self):
        response = self.app.get(
            '/election/2015/person/create/',
            user=self.user
        )
        form = response.forms['new-candidate-form']
        form['name'] = 'Naomi Newperson'
        form['additional_link'] = 'http://example.com/morelink'
        form['standing_2015'] = 'not-standing'
        form['source'] = 'Test creating someone with simple fields'
        submission_response = form.submit()

        self.assertEqual(submission_response.status_code, 302)
        split_location = urlsplit(submission_response.location)
        m = re.search(r'^/person/(.*)', split_location.path)
        self.assertTrue(m)

        person = Person.objects.get(id=m.group(1))
        self.assertEqual(person.extra.additional_link, 'http://example.com/morelink')

    def test_view_additional_fields(self):
        response = self.app.get(
            '/person/{person_id}'.format(person_id=self.person.id)
        )

        an_dt = response.html.find('dt', text=u'Additional Link')
        an_dd = get_next_dd(an_dt)
        self.assertEqual(an_dd.text.strip(), 'http://example.com/additional')

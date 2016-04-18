# -*- coding: utf-8 -*-
from django.test import TestCase

from candidates.models import PersonExtra, ComplexPopoloField
from popolo.models import Person
from tasks.models import PersonTask


class PersonTaskTests(TestCase):

    def setUp(self):
        # Create one person with these fields already present:
        self.person = Person.objects.create(
            name="John the Well-Described",
            additional_name="Very Well-Described"
        )
        PersonExtra.objects.create(base=self.person, versions='[]')
        PersonTask.objects.create(
            task_field='email',
            person=self.person,
        )
        PersonTask.objects.create(
            task_field='facebook_page_url',
            person=self.person,
        )

    def test_task_updated_on_save(self):
        self.assertEqual(PersonTask.objects.unfinished_tasks().count(), 2)
        self.person.email = "a@example.com"
        self.person.save()

        self.person.extra.save()
        self.assertEqual(PersonTask.objects.unfinished_tasks().count(), 1)

    def test_task_updated_complex_field(self):
        self.assertEqual(PersonTask.objects.unfinished_tasks().count(), 2)
        self.person.email = "a@example.com"
        facebook_field = ComplexPopoloField.objects.get(
            name="facebook_page_url")
        self.person.extra.update_complex_field(
            facebook_field, 'https://facebook.com/example')
        twitter_field = ComplexPopoloField.objects.get(
            name="twitter_username")
        self.person.extra.update_complex_field(
            twitter_field, 'https://twitter.com/example')

        self.person.save()
        self.person.extra.save()

        self.assertEqual(PersonTask.objects.unfinished_tasks().count(), 0)


    def test_task_could_not_find(self):
        task = PersonTask.objects.all().first()
        self.assertEqual(task.couldnt_find_count, 0)
        self.assertEqual(task.bonus_points, 1)

        task.log_not_found()
        task.refresh_from_db()
        self.assertEqual(task.bonus_points, 2)
        task.log_not_found()
        task.refresh_from_db()
        self.assertEqual(task.bonus_points, 4)

from __future__ import unicode_literals
import json

from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User

from django_extensions.db.models import TimeStampedModel

from popolo.models import Person
from candidates.models import (PersonExtra, ComplexPopoloField,
                               SimplePopoloField)


class PersonTaskManager(models.Manager):
    def unfinished_tasks(self):
        return self.filter(found=False)


class PersonTask(TimeStampedModel):
    task_field = models.CharField(blank=True, max_length=100)
    task_priority = models.IntegerField(blank=True, null=True, default=1)
    person = models.ForeignKey(Person)
    finder = models.ForeignKey(User, null=True)
    found = models.BooleanField(default=False)
    bonus_points = models.IntegerField(blank=True, null=True, default=1)
    couldnt_find_count = models.IntegerField(blank=True, null=True, default=0)

    objects = PersonTaskManager()

    class Meta:
        ordering = ['-task_priority', ]

    def get_user_from_vesions(self):
        version_data = json.loads(self.person.extra.versions)
        if not version_data or 'username' not in version_data[0]:
            return None
        try:
            return User.objects.get(username=version_data[0]['username'])
        except User.DoesNotExist:
            return None

    def get_value_from_person(self):
        value = getattr(self.person, self.task_field, None)
        if value:
            return value

        person_qs = PersonExtra.objects.filter(base=self.person)
        simple_field = SimplePopoloField.objects.filter(
            name=self.task_field).first()
        if simple_field:
            return person_qs.filter(**{'base__' + self.task_field: ''})


        complex_field = ComplexPopoloField.objects.filter(
            name=self.task_field).first()

        if complex_field:
            kwargs = {
                'base__{relation}__{key}'.format(
                    relation=complex_field.popolo_array,
                    key=complex_field.info_type_key
                ):
                complex_field.info_type
            }
            return person_qs.filter(**kwargs)

    def log_not_found(self):
        self.couldnt_find_count += 1
        self.bonus_points = self.bonus_points * 2
        self.save()


def person_saved(sender, **kwargs):
    person_tasks = PersonTask.objects.filter(person=kwargs['instance'].base)
    for task in person_tasks:
        field_value = task.get_value_from_person()
        if field_value:
            task.finder = task.get_user_from_vesions()
            task.found = True
            task.save()

post_save.connect(person_saved, sender=PersonExtra)

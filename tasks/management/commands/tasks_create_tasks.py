from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction


from candidates.models import PersonExtra
from tasks.models import PersonTask


class Command(BaseCommand):
    FIELD_WEIGHT = {
        'homepage_url': 30,
        'email': 20,
        'twitter_username': 15,
        'facebook_page_url': 15,
    }

    ELECTION_WEIGHT = {
        'local': 1,
        'gla.a': 1,
        'gla.c': 60,
        'mayor': 100,
        'parl': 200,
        'naw.c': 50,
        'naw.r': 10,
        'nia': 1,
        'pcc': 50,
        'sp.c': 80,
        'sp.r': 10,
    }

    def handle(self, **options):
        for field, field_weight in self.FIELD_WEIGHT.items():
            self.add_tasks_for_field(field, field_weight)

    def override_election_weight(self, election):
        if election.in_past:
            return -100
        days_to_election = election.election_date - date.today()
        if days_to_election.days >= 40 and days_to_election.days <= 80:
            return 50
        if days_to_election.days >= 0 and days_to_election.days <= 40:
            return 100
        return 0

    @transaction.atomic
    def add_tasks_for_field(self, field, field_weight):
        qs = PersonExtra.objects.filter(
            base__memberships__extra__election__current=True)
        qs = qs.select_related('base')
        qs = qs.prefetch_related('base__memberships')
        qs = qs.missing(field)

        person_tasks = []

        PersonTask.objects.filter(task_field=field).delete()

        for person in qs:
            person_weight = 0
            membership_qs = person.base.memberships.all()
            membership_qs = membership_qs.select_related(
                'post__extra'
            ).prefetch_related('post__extra__elections')
            for membership in membership_qs:
                try:
                    getattr(membership.post, 'extra')
                except:
                    continue
                for election in membership.post.extra.elections.filter(current=True):
                    for election_id, election_weight in self.ELECTION_WEIGHT.items():
                        election_weight += self.override_election_weight(
                            election
                        )
                        if election.slug.startswith(election_id):
                            person_weight += election_weight
                            person_weight += field_weight
                            person_tasks.append(
                                PersonTask(
                                    person=person.base,
                                    task_field=field,
                                    task_priority=person_weight,
                                )
                            )
        PersonTask.objects.bulk_create(person_tasks)

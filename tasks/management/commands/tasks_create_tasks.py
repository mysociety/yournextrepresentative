from django.core.management.base import BaseCommand


from candidates.models import PersonExtra
from tasks.models import PersonTask


class Command(BaseCommand):
    FIELD_WEIGHT = {
        'email': 20,
        'twitter_username': 15,
        'facebook_page_url': 15,
    }

    ELECTION_WEIGHT = {
        'local': 1,
        'gla.a': 1,
        'gla.c': 60,
        'mayor.bristol': 90,
        'mayor.liverpool': 80,
        'mayor.london': 100,
        'mayor.salford': 80,
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


    def add_tasks_for_field(self, field, field_weight):
        for person in PersonExtra.objects.missing(field):
            person_weight = 0
            for membership in person.base.memberships.all():
                try:
                    getattr(membership.post, 'extra')
                except:
                    continue
                for election in membership.post.extra.elections.all():
                    for election_id, election_weight in self.ELECTION_WEIGHT.items():
                        if election.slug.startswith(election_id):
                            person_weight += election_weight
                            person_weight += field_weight
                            PersonTask.objects.update_or_create(
                                person=person.base,
                                task_field=field,
                                defaults={
                                    'task_priority': person_weight
                                }
                            )

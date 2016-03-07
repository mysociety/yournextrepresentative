from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.db import transaction

from elections.models import Election


class Command(BaseCommand):

    help = 'Fix the mixup of UK regional / constituency elections'

    def handle(self, **options):
        with transaction.atomic():
            # ----------------------------------------------------------------
            # The Scottish mixup:
            sp_should_be_c = Election.objects.get(slug='sp.r.2016-05-05')
            sp_should_be_r = Election.objects.get(slug='sp.c.2016-05-05')
            # Constituencies first; we have to use a temporary slug
            # name because of the unique constraint on slug:
            sp_should_be_c.slug = 'sp.c.2016-05-05-new'
            sp_should_be_c.name = '2016 Scottish Parliament Election (Constituencies)'
            sp_should_be_c.party_lists_in_use = False
            sp_should_be_c.save()
            # Now regions:
            sp_should_be_r.slug = 'sp.r.2016-05-05'
            sp_should_be_r.name = '2016 Scottish Parliament Election (Regions)'
            sp_should_be_r.party_lists_in_use = True
            sp_should_be_r.save()
            # Now fix the slug for the constituencies election:
            sp_should_be_c.slug = 'sp.c.2016-05-05'
            sp_should_be_c.save()
            # Now save them:
            # ----------------------------------------------------------------
            # The Wales mixup:
            wa_should_be_c = Election.objects.get(slug='naw.r.2016-05-05')
            wa_should_be_r = Election.objects.get(slug='naw.c.2016-05-05')
            # Constituencies first; we have to use a temporary slug
            # name because of the unique constraint on slug:
            wa_should_be_c.slug = 'naw.c.2016-05-05-new'
            wa_should_be_c.name = '2016 Welsh Assembly Election (Constituencies)'
            wa_should_be_c.party_lists_in_use = False
            wa_should_be_c.save()
            # Now regions:
            wa_should_be_r.slug = 'naw.r.2016-05-05'
            wa_should_be_r.name = '2016 Welsh Assembly Election (Regions)'
            wa_should_be_r.party_lists_in_use = True
            wa_should_be_r.save()
            # Now save them:
            wa_should_be_c.slug = 'naw.c.2016-05-05'
            wa_should_be_c.save()

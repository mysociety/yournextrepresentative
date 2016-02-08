import re
import pytz
from datetime import datetime, timedelta

from django_webtest import WebTest
from django.core import mail
from django.core.management import call_command

from candidates.tests.factories import (
    AreaTypeFactory, ElectionFactory, CandidacyExtraFactory,
    ParliamentaryChamberFactory, PartyFactory, PartyExtraFactory,
    PersonExtraFactory, PostExtraFactory, PartySetFactory,
    AreaExtraFactory
)

from django.contrib.contenttypes.models import ContentType

from candidates.tests.auth import TestUserMixin

from .models import Alert


class AlertsTest(TestUserMixin, WebTest):

    def setUp(self):
        wmc_area_type = AreaTypeFactory.create()
        gb_parties = PartySetFactory.create(slug='gb', name='Great Britain')
        election = ElectionFactory.create(
            slug='2015',
            name='2015 General Election',
            area_types=(wmc_area_type,)
        )
        area_extra = AreaExtraFactory.create(
            base__name="Dulwich and West Norwood",
            type=wmc_area_type,
        )
        commons = ParliamentaryChamberFactory.create()
        post_extra = PostExtraFactory.create(
            elections=(election,),
            base__area=area_extra.base,
            base__organization=commons,
            slug='65808',
            party_set=gb_parties,
            base__label='Member of Parliament for Dulwich and West Norwood'
        )
        camberwell_area_extra = AreaExtraFactory.create(
            base__identifier='65913',
            type=wmc_area_type,
        )
        camberwell_post = PostExtraFactory.create(
            elections=(election,),
            base__area=camberwell_area_extra.base,
            base__organization=commons,
            slug='65913',
            candidates_locked=True,
            base__label='Member of Parliament for Camberwell and Peckham',
            party_set=gb_parties,
        )
        person_extra = PersonExtraFactory.create(
            base__id='2009',
            base__name='Tessa Jowell'
        )
        self.person = person_extra.base

        PartyExtraFactory.reset_sequence()
        PartyFactory.reset_sequence()
        self.parties = {}
        for i in range(0, 4):
            party_extra = PartyExtraFactory.create()
            gb_parties.parties.add(party_extra.base)
            self.parties[party_extra.slug] = party_extra

        CandidacyExtraFactory.create(
            election=election,
            base__person=person_extra.base,
            base__post=post_extra.base,
            base__on_behalf_of=self.parties['party:63'].base
        )

        person_extra = PersonExtraFactory.create(
            base__id='2010',
            base__name='Angela Smith'
        )
        self.person2 = person_extra.base

        CandidacyExtraFactory.create(
            election=election,
            base__person=person_extra.base,
            base__post=post_extra.base,
            base__on_behalf_of=self.parties['party:63'].base
        )

        content_type = ContentType.objects.get_for_model(person_extra.base)

        last_sent = datetime.now(pytz.utc) - timedelta(days=2)
        self.alert = Alert.objects.create(
            user=self.user,
            target_content_type=content_type,
            target_object_id=self.person.id,
            last_sent=last_sent,
            frequency='hourly'
        )

        self.alert2 = Alert.objects.create(
            user=self.user_who_can_lock,
            target_content_type=content_type,
            target_object_id=self.person2.id,
            last_sent=last_sent,
            frequency='daily'
        )

        person_extra = PersonExtraFactory.create(
            base__id='2011',
            base__name='Martin Jones'
        )
        self.person2 = person_extra.base

        CandidacyExtraFactory.create(
            election=election,
            base__person=person_extra.base,
            base__post=camberwell_post.base,
            base__on_behalf_of=self.parties['party:63'].base
        )

        content_type = ContentType.objects.get_for_model(
            camberwell_area_extra.base
        )
        self.alert3 = Alert.objects.create(
            user=self.user_who_can_merge,
            target_content_type=content_type,
            target_object_id=camberwell_area_extra.base.id,
            last_sent=last_sent,
            frequency='daily'
        )

        aldershot_area_extra = AreaExtraFactory.create(
            base__identifier='65730',
            type=wmc_area_type,
        )

        aldershot_post = PostExtraFactory.create(
            elections=(election,),
            base__area=aldershot_area_extra.base,
            base__organization=commons,
            slug='65730',
            base__label='Member of Parliament for Aldershot',
            party_set=gb_parties,
        )

        person_extra = PersonExtraFactory.create(
            base__id='2012',
            base__name='Gillian Collins'
        )
        self.person3 = person_extra.base

        CandidacyExtraFactory.create(
            election=election,
            base__person=person_extra.base,
            base__post=aldershot_post.base,
            base__on_behalf_of=self.parties['party:63'].base
        )

        content_type = ContentType.objects.get_for_model(
            self.parties['party:90'].base
        )

        self.alert4 = Alert.objects.create(
            user=self.user_who_can_rename,
            target_content_type=content_type,
            target_object_id=self.parties['party:90'].base.id,
            last_sent=last_sent,
            frequency='daily'
        )

        content_type = ContentType.objects.get_for_model(
            camberwell_area_extra.base
        )

        self.alert5 = Alert.objects.create(
            user=self.user,
            target_content_type=content_type,
            target_object_id=66101,
            last_sent=last_sent,
            frequency='hourly'
        )

    def tearDown(self):
        self.alert.delete()
        self.alert2.delete()
        self.alert3.delete()
        self.alert4.delete()
        self.alert5.delete()

    def test_send_hourly(self):
        response = self.app.get(
            '/person/2009/update',
            user=self.user_who_can_lock,
        )
        form = response.forms['person-details']
        form['honorific_prefix'] = 'Ms'
        form['source'] = "test_send_hourly"
        form.submit()

        response = self.app.get(
            '/person/2010/update',
            user=self.user_who_can_lock,
        )
        form = response.forms['person-details']
        form['honorific_prefix'] = 'Mrs'
        form['source'] = "test_send_daily"
        response = form.submit()

        call_command('alerts_send_alerts', '--hourly')

        self.assertEquals(len(mail.outbox), 1)
        msg = mail.outbox[0]

        self.assertTrue(re.search(r'Changes to Tessa Jowell', msg.body))
        self.assertTrue(re.search(r'(?ms)honorific_prefix', msg.body))
        self.assertFalse(re.search(r'Changes to Angela Smith', msg.body))

    def test_send_daily(self):
        response = self.app.get(
            '/person/2009/update',
            user=self.user_who_can_lock,
        )
        form = response.forms['person-details']
        form['honorific_prefix'] = 'Ms'
        form['source'] = "test_send_hourly"
        form.submit()

        response = self.app.get(
            '/person/2010/update',
            user=self.user_who_can_lock,
        )
        form = response.forms['person-details']
        form['honorific_prefix'] = 'Mrs'
        form['source'] = "test_send_daily"
        response = form.submit()

        call_command('alerts_send_alerts', '--daily')

        self.assertEquals(len(mail.outbox), 1)
        msg = mail.outbox[0]

        self.assertTrue(re.search(r'Changes to Angela Smith', msg.body))
        self.assertTrue(re.search(r'(?ms)honorific_prefix', msg.body))
        self.assertFalse(re.search(r'Changes to Tessa Jowell', msg.body))

    def test_send_area(self):
        response = self.app.get(
            '/person/2011/update',
            user=self.user_who_can_lock,
        )
        form = response.forms['person-details']
        form['honorific_prefix'] = 'Mr'
        form['source'] = "test_send_area"
        response = form.submit()

        call_command('alerts_send_alerts', '--daily')

        self.assertEquals(len(mail.outbox), 1)
        msg = mail.outbox[0]

        self.assertTrue(re.search(r'Changes to Martin Jones', msg.body))
        self.assertTrue(re.search(r'(?ms)honorific_prefix', msg.body))

    def test_send_party(self):
        response = self.app.get(
            '/person/2012/update',
            user=self.user_who_can_lock,
        )
        form = response.forms['person-details']
        form['party_gb_2015'] = self.parties['party:90'].base.id
        form['source'] = "test_send_area"
        response = form.submit()

        call_command('alerts_send_alerts', '--daily')

        self.assertEquals(len(mail.outbox), 1)
        msg = mail.outbox[0]

        self.assertTrue(re.search(r'Changes to Gillian Collins', msg.body))
        self.assertTrue(re.search(r'(?ms)party_memberships', msg.body))

    def test_only_one_mention_for_two_alerts(self):
        response = self.app.get(
            '/person/2009/update',
            user=self.user_who_can_lock,
        )
        form = response.forms['person-details']
        form['constituency_2015'] = '65913'
        form['source'] = "test_send_hourly"
        form.submit()

        call_command('alerts_send_alerts', '--hourly')

        self.assertEquals(len(mail.outbox), 1)

        msg = mail.outbox[0]

        self.assertEquals(len(re.findall(r'Changes to Tessa Jowell', msg.body)), 1)

    def test_sends_multiple_alerts(self):
        response = self.app.get(
            '/person/2010/update',
            user=self.user_who_can_lock,
        )
        form = response.forms['person-details']
        form['constituency_2015'] = '65913'
        form['source'] = "test_sends_multiple_alerts"
        form.submit()

        call_command('alerts_send_alerts', '--daily')

        self.assertEquals(len(mail.outbox), 2)

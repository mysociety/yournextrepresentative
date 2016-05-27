import re
import pytz
from datetime import datetime, timedelta

from django_webtest import WebTest
from django.core import mail
from django.core.management import call_command
from django.test.utils import override_settings

from nose.plugins.attrib import attr

from candidates.tests.factories import (
    AreaExtraFactory, CandidacyExtraFactory, PersonExtraFactory,
    PostExtraFactory,
)
from candidates.tests.settings import SettingsMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin

from django.contrib.contenttypes.models import ContentType

from candidates.models import LoggedAction
from candidates.tests.auth import TestUserMixin

from .models import Alert


class AlertsTest(TestUserMixin, SettingsMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(AlertsTest, self).setUp()
        person_extra = PersonExtraFactory.create(
            base__id='2009',
            base__name='Tessa Jowell'
        )
        self.person = person_extra.base

        CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.green_party_extra.base
        )

        person_extra = PersonExtraFactory.create(
            base__id='2010',
            base__name='Angela Smith'
        )
        self.person2 = person_extra.base

        CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.green_party_extra.base
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
            election=self.election,
            base__person=person_extra.base,
            base__post=self.camberwell_post_extra.base,
            base__on_behalf_of=self.green_party_extra.base
        )

        content_type = ContentType.objects.get_for_model(
            self.camberwell_post_extra.base.area
        )
        self.alert3 = Alert.objects.create(
            user=self.user_who_can_merge,
            target_content_type=content_type,
            target_object_id=self.camberwell_post_extra.base.area.id,
            last_sent=last_sent,
            frequency='daily'
        )

        aldershot_area_extra = AreaExtraFactory.create(
            base__identifier='65730',
            type=self.wmc_area_type,
        )

        aldershot_post = PostExtraFactory.create(
            elections=(self.election,),
            base__area=aldershot_area_extra.base,
            base__organization=self.commons,
            slug='65730',
            base__label='Member of Parliament for Aldershot',
            party_set=self.gb_parties,
        )

        person_extra = PersonExtraFactory.create(
            base__id='2012',
            base__name='Gillian Collins'
        )
        self.person3 = person_extra.base

        CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_extra.base,
            base__post=aldershot_post.base,
            base__on_behalf_of=self.green_party_extra.base
        )

        content_type = ContentType.objects.get_for_model(
            self.ld_party_extra.base
        )

        self.alert4 = Alert.objects.create(
            user=self.user_who_can_rename,
            target_content_type=content_type,
            target_object_id=self.ld_party_extra.base.id,
            last_sent=last_sent,
            frequency='daily'
        )

        content_type = ContentType.objects.get_for_model(
            self.camberwell_post_extra.base.area
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
        form['party_gb_2015'] = self.ld_party_extra.base.id
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

    @override_settings(LANGUAGE_CODE='es-cr')
    @attr(country='cr')
    def test_email_translated(self):
        response = self.app.get(
            '/person/2010/update',
            user=self.user_who_can_lock,
        )
        form = response.forms['person-details']
        form['honorific_prefix'] = 'Mrs'
        form['source'] = "test_email_translated"
        response = form.submit()

        call_command('alerts_send_alerts', '--daily')

        self.assertEquals(len(mail.outbox), 1)
        msg = mail.outbox[0]

        self.assertTrue(re.search(r'Angela Smith', msg.body))
        self.assertTrue(re.search(r'Agregado', msg.body))

    def test_change_with_no_details(self):
        la = LoggedAction.objects.create(
            user=self.user_who_can_lock,
            person=self.person,
            action_type='person-update',
            source="test_change_with_no_details"
        )

        call_command('alerts_send_alerts', '--hourly')

        self.assertEquals(len(mail.outbox), 1)
        msg = mail.outbox[0]

        self.assertTrue(re.search(r'Tessa Jowell', msg.body))
        self.assertTrue(re.search(r'There has been 1 change we don', msg.body))

        la.delete()

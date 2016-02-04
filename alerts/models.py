from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from notifications.signals import notify

from popolo.models import Membership
from candidates.models import PostExtra, LoggedAction


class Alert(models.Model):
    user = models.ForeignKey(User)

    target_content_type = models.ForeignKey(
        ContentType,
        related_name='alert_target',
        blank=True,
        null=True
    )
    target_object_id = models.CharField(max_length=255, blank=True, null=True)
    target = GenericForeignKey('target_content_type', 'target_object_id')

    action = models.CharField(
        max_length=100,
        choices=(
            ('created', 'Created'),
            ('updated', 'Updated'),
            ('deleted', 'Deleted'),
            ('image_update', 'Images'),
            ('all', 'All'),
        )
    )

    frequency = models.CharField(
        max_length=100,
        choices=(
            ('hourly', 'Hourly'),
            ('daily', 'Daily')
        )
    )
    last_sent = models.DateTimeField()
    enabled = models.BooleanField(default=True)


def send_person_signals(sender, instance, created, **kwargs):
    """
    This creates the notifications we use to send email alerts of
    changes to people
    """
    if instance.action_type not in (
        'person-update', 'person-create'
    ):
        return

    person = instance.person
    content_type = ContentType.objects.get_for_model(person)
    verb = 'updated'
    if created:
        verb = 'created'

    alerts = Alert.objects.filter(
        target_content_type=content_type,
        target_object_id=person.id
    )

    users_alerted = set()

    # This is here to make writing tests a bit easier as
    # it means you don't need to create a versions object
    # or add an extra if it's not required
    try:
        changes = person.extra.version_diffs[0]
    except (IndexError, ObjectDoesNotExist):
        changes = None

    for alert in alerts:
        if alert.user not in users_alerted:
            users_alerted.add(alert.user)
            notify.send(
                instance.user,
                action_object=person,
                verb=verb,
                recipient=alert.user,
                changes=changes
            )

    # FIXME: this doesn't handle people being removed from an area
    posts = PostExtra.objects.filter(
        base__memberships__person=person,
        elections__current=True
    )

    for post in posts:
        area = post.base.area
        if area is not None:
            content_type = ContentType.objects.get_for_model(area)
            alerts = Alert.objects.filter(
                target_content_type=content_type,
                target_object_id=area.id
            )

            for alert in alerts:
                if alert.user not in users_alerted:
                    users_alerted.add(alert.user)
                    notify.send(
                        instance.user,
                        action_object=person,
                        verb=verb,
                        recipient=alert.user,
                        changes=changes
                    )

    # TODO: not sure this is the correct way to do this
    memberships = Membership.objects.filter(
        person=person,
        on_behalf_of__classification='Party',
        extra__election__current=True
    )

    for membership in memberships:
        party = membership.on_behalf_of
        if party is not None:
            content_type = ContentType.objects.get_for_model(party)
            alerts = Alert.objects.filter(
                target_content_type=content_type,
                target_object_id=party.id
            )

            for alert in alerts:
                if alert.user not in users_alerted:
                    users_alerted.add(alert.user)
                    notify.send(
                        instance.user,
                        action_object=person,
                        verb=verb,
                        recipient=alert.user,
                        changes=changes
                    )

post_save.connect(send_person_signals, sender=LoggedAction)

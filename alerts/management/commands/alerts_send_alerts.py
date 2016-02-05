from dateutil import parser
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string

from alerts.models import Alert


class Command(BaseCommand):

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            '--hourly',
            action='store_true',
            help='Send hourly alerts'
        )
        group.add_argument(
            '--daily',
            action='store_true',
            help='Send daily alerts'
        )

    def handle(self, **options):
        if options['hourly']:
            last_sent = datetime.utcnow() - timedelta(hours=1)
            frequency = 'hourly'
        elif options['daily']:
            last_sent = datetime.utcnow() - timedelta(days=1)
            frequency = 'daily'

        alerts = Alert.objects.filter(
            frequency=frequency,
            last_sent__lt=last_sent
        )

        """
        at the moment this means that if a user has multiple alerts set up
        they will get all of them in the same email, even if they have set
        up one alert to be daily and one to be hourly
        """
        for alert in alerts:
            events = alert.user.notifications.unread() \
                .order_by('action_object_content_type', 'action_object_object_id')

            details = ""
            current_object = ''
            if events.count() > 0:
                no_change_count = 0
                change_count = 0
                for event in events:
                    if event.action_object != current_object:
                        if current_object != '':
                            details += "\n"
                        details += 'Changes to {0}\n'.format(event.action_object)
                        domain = Site.objects.get_current().domain
                        path = reverse(
                            'person-view',
                            kwargs={'person_id': event.action_object.id}
                        )
                        protocol = 'http'
                        if hasattr(settings, 'ACCOUNT_DEFAULT_HTTP_PROTOCOL') and \
                            settings.ACCOUNT_DEFAULT_HTTP_PROTOCOL == 'https':
                            protocol = 'https'
                        details += "{0}://{1}{2}\n".format(
                            protocol,
                            domain,
                            path
                        )
                        current_object = event.action_object
                    if event.data:
                        if event.data['changes'] is not None:
                            timestamp = parser.parse(event.data['changes']['timestamp'])
                            event.data['changes']['timestamp'] = timestamp
                            diff = render_to_string('alerts/pretty_diff.txt', context=event.data)
                            # remove extra blank lines
                            diff = "\n".join([ll.rstrip() for ll in diff.splitlines() if ll.strip()])
                            details += "\n{0}\n".format(diff)
                            change_count += 1
                        else:
                            no_change_count += 1
                    else:
                        no_change_count += 1

                if no_change_count == 1:
                    if details:
                        details += "\nAnd 1 change we don't have details of\n"
                    else:
                        details += "\nThere has been 1 change we don't have details of\n"
                elif no_change_count > 1:
                    if details:
                        details += "\nAnd {0} changes we don't have details of\n".format(no_change_count)
                    else:
                        details += "\nThere have been {0} changes we don't have details of\n".format(no_change_count)

                recipients = [alert.user.email]
                has_sent = send_mail(
                    "Recent activity on YNR",
                    details,
                    settings.DEFAULT_FROM_EMAIL,
                    recipients,
                    fail_silently=False,
                )

                if has_sent:
                    alert.last_sent = datetime.utcnow()
                    alert.save()

                    events.mark_all_as_read()

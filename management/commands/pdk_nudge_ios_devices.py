# pylint: disable=no-member,line-too-long

from pushjack import APNSClient, APNSSandboxClient

from django.conf import settings

from django.core.management.base import BaseCommand

from ...decorators import handle_lock
from ...models import DataPoint

class Command(BaseCommand):
    help = 'Send silent notifications to iOS devices to nudge power management systems for transmission.'

    def add_arguments(self, parser):
        pass

    @handle_lock
    def handle(self, *args, **options):
        apns = APNSClient(certificate=settings.PDK_APNS_CERTIFICATE)

        if settings.PDK_APNS_IS_SANDBOX:
            apns = APNSSandboxClient(certificate=settings.PDK_APNS_CERTIFICATE)

        expired = []

        exp_tokens = apns.get_expired_tokens()

        for token in exp_tokens:
            expired.append(token.token)

        tokens = {}

        for point in DataPoint.objects.filter(generator_identifier='pdk-app-event', secondary_identifier='pdk-ios-device-token').order_by('created'):
            properties = point.fetch_properties()

            tokens[point.source] = properties['event_details']['token']

            if tokens[point.source] in expired:
                print 'RENAMING TOKEN FOR ' + point.source

                point.secondary_identifier = 'pdk-ios-device-token-expired'
                point.save()

        token_list = []

        for source, token in tokens.iteritems(): # pylint: disable=unused-variable
            if (token in token_list) is False and (token in expired) is False:
                token_list.append(token)

        notification = {'source': 'passive-data-kit', 'operation': 'nudge'}

        apns.send(token_list, notification, content_available=True)

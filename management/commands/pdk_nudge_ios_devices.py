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

        # print('EXPIRED: ' + str(apns.get_expired_tokens()))

        tokens = {}

        for point in DataPoint.objects.filter(generator_identifier='pdk-app-event', secondary_identifier='pdk-ios-device-token').order_by('created'):
            properties = point.fetch_properties()

            tokens[point.source] = properties['event_details']['token']

        token_list = []

        for source, token in tokens.iteritems(): # pylint: disable=unused-variable
            if (token in token_list) is False:
                token_list.append(token)

        notification = {'aps': {'operation' : 'nudge'}, 'source': 'passive-data-kit'}

        apns.send(token_list, notification)

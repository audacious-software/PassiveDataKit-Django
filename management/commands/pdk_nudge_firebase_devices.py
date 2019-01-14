# pylint: disable=no-member,line-too-long

from pyfcm import FCMNotification

from django.conf import settings

from django.core.management.base import BaseCommand

from ...decorators import handle_lock
from ...models import DataPoint

class Command(BaseCommand):
    help = 'Send silent notifications to Android Firebase devices to nudge power management systems for transmission.'

    def add_arguments(self, parser):
        pass

    @handle_lock
    def handle(self, *args, **options):
        push_service = FCMNotification(api_key=settings.PDK_FIREBASE_API_KEY)

        tokens = {}

        for point in DataPoint.objects.filter(generator_identifier='pdk-app-event', secondary_identifier='pdk-firebase-token').order_by('created'):
            properties = point.fetch_properties()

            tokens[point.source] = properties['event_details']['token']

        token_list = []

        for source, token in tokens.iteritems(): # pylint: disable=unused-variable
            if (token in token_list) is False:
                token_list.append(token)

        message = {'operation' : 'nudge', 'source': 'passive-data-kit'}

        push_service.notify_multiple_devices(registration_ids=token_list, data_message=message)

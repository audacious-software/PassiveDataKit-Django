# pylint: disable=no-member,line-too-long

from pyfcm import FCMNotification

from django.conf import settings

from django.core.management.base import BaseCommand

from ...decorators import handle_lock
from ...models import DataPoint, DataGeneratorDefinition

class Command(BaseCommand):
    help = 'Send silent notifications to Android Firebase devices to nudge power management systems for transmission.'

    def add_arguments(self, parser):
        pass

    @handle_lock
    def handle(self, *args, **options):
        push_service = FCMNotification(api_key=settings.PDK_FIREBASE_API_KEY)

        event_definition = DataGeneratorDefinition.definition_for_identifier('pdk-app-event')

        tokens = {}

        for point in DataPoint.objects.filter(generator_definition=event_definition, secondary_identifier='pdk-firebase-token').order_by('created'):
            properties = point.fetch_properties()

            tokens[point.source] = properties['event_details']['token']

        token_list = []

        for source, token in tokens.iteritems(): # pylint: disable=unused-variable
            if (token in token_list) is False:
                token_list.append(token)

        message = {'operation' : 'nudge', 'source': 'passive-data-kit'}

        result = push_service.notify_multiple_devices(registration_ids=token_list, data_message=message)

        if settings.DEBUG:
            print 'Firebase nudge result: ' + str(result)
            print '(Update settings.DEBUG to suppress...)'

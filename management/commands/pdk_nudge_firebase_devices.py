# pylint: disable=no-member,line-too-long

import datetime

from pyfcm import FCMNotification

from django.conf import settings

from django.core.management.base import BaseCommand
from django.utils import timezone

from ...decorators import handle_lock, log_scheduled_event
from ...models import DataPoint, DataGeneratorDefinition, DataSourceReference, DataSource

class Command(BaseCommand):
    help = 'Send silent notifications to Android Firebase devices to nudge power management systems for transmission.'

    def add_arguments(self, parser):
        pass

    @handle_lock
    @log_scheduled_event
    def handle(self, *args, **options): # pylint: disable=too-many-locals
        push_service = FCMNotification(api_key=settings.PDK_FIREBASE_API_KEY)

        event_definition = DataGeneratorDefinition.definition_for_identifier('pdk-app-event')

        count = DataSource.objects.all().count()

        index = 0

        active_days_window = 14

        try:
            active_days_window = settings.PDK_NOTIFICATION_ACTIVE_DAYS_WINDOW
        except AttributeError:
            pass

        window_start = timezone.now() - datetime.timedelta(days=active_days_window)

        while index < count:
            tokens = {}

            for source in DataSource.objects.all().order_by('identifier')[index:(index+128)]:
                source_reference = DataSourceReference.reference_for_source(source.identifier)

                latest_point = source.latest_point()

                if latest_point is not None and latest_point.created > window_start:
                    point = DataPoint.objects.filter(generator_definition=event_definition, source_reference=source_reference, secondary_identifier='pdk-firebase-token', created__gte=window_start).order_by('-created').first()

                    if point is not None:
                        properties = point.fetch_properties()

                        tokens[source.identifier] = properties['event_details']['token']

            token_list = []

            for source, token in tokens.iteritems(): # pylint: disable=unused-variable
                if (token in token_list) is False:
                    token_list.append(token)

            message = {'operation' : 'nudge', 'source': 'passive-data-kit'}

            result = push_service.notify_multiple_devices(registration_ids=token_list, data_message=message)

            index += 128

        if settings.DEBUG:
            print 'Firebase nudge result: ' + str(result)
            print '(Update settings.DEBUG to suppress...)'

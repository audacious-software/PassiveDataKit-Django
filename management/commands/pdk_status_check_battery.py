# pylint: disable=line-too-long, no-member

from django.core.management.base import BaseCommand
from django.utils import timezone

from ...decorators import handle_lock

from ...models import DataPoint, DataSource, DataSourceAlert

GENERATOR = 'pdk-device-battery'
CRITICAL_LEVEL = 20
WARNING_LEVEL = 33

class Command(BaseCommand):
    help = 'Runs the battery level status check to alert when battery level is low.'

    @handle_lock
    def handle(self, *args, **options): # pylint: disable=too-many-branches, too-many-statements
        for source in DataSource.objects.all():
            last_battery = DataPoint.objects.filter(source=source.identifier, generator_identifier=GENERATOR).order_by('-created').first()
            last_alert = DataSourceAlert.objects.filter(data_source=source, generator_identifier=GENERATOR, active=True).order_by('-created').first()

            alert_name = None
            alert_details = {}
            alert_level = 'info'

            if last_battery is not None:
                properties = last_battery.fetch_properties()

                if properties['level'] < CRITICAL_LEVEL:
                    alert_name = 'Battery Level Critically Low'
                    alert_details['message'] = 'Latest battery level is ' + str(properties['level']) + '%.'
                    alert_level = 'critical'

                elif properties['level'] < WARNING_LEVEL:
                    alert_name = 'Battery Level Low'
                    alert_details['message'] = 'Latest battery level is ' + str(properties['level']) + '%.'
                    alert_level = 'warning'

                if alert_name is not None:
                    if last_alert is None or last_alert.alert_name != alert_name or last_alert.alert_level != alert_level:
                        if last_alert is not None:
                            last_alert.active = False
                            last_alert.updated = timezone.now()
                            last_alert.save()

                        new_alert = DataSourceAlert(alert_name=alert_name, data_source=source, generator_identifier=GENERATOR)
                        new_alert.alert_level = alert_level
                        new_alert.update_alert_details(alert_details)
                        new_alert.created = timezone.now()
                        new_alert.updated = timezone.now()
                        new_alert.active = True

                        new_alert.save()
                    else:
                        last_alert.updated = timezone.now()
                        last_alert.update_alert_details(alert_details)

                        last_alert.save()
                elif last_alert is not None:
                    last_alert.updated = timezone.now()
                    last_alert.active = False

                    last_alert.save()
            else:
                alert_name = 'No Battery Levels Logged'
                alert_details['message'] = 'No battery levels have been logged for this device yet.'

                if last_alert is None or last_alert.alert_name != alert_name or last_alert.alert_level != alert_level:
                    if last_alert is not None:
                        last_alert.active = False
                        last_alert.updated = timezone.now()
                        last_alert.save()

                    new_alert = DataSourceAlert(alert_name=alert_name, data_source=source, generator_identifier=GENERATOR)
                    new_alert.alert_level = alert_level
                    new_alert.update_alert_details(alert_details)
                    new_alert.created = timezone.now()
                    new_alert.updated = timezone.now()
                    new_alert.active = True

                    new_alert.save()
                else:
                    last_alert.updated = timezone.now()
                    last_alert.update_alert_details(alert_details)

                    last_alert.save()

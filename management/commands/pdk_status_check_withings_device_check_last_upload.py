# pylint: disable=line-too-long, no-member

from django.core.management.base import BaseCommand
from django.utils import timezone

from ...decorators import handle_lock

from ...models import DataPoint, DataSource, DataSourceAlert

GENERATOR = 'pdk-withings-device'
CRITICAL_DAYS = 2
WARNING_DAYS = 1

class Command(BaseCommand):
    help = 'Runs the Withings device upload status check to alert when a device sync is overdue.'

    @handle_lock
    def handle(self, *args, **options): # pylint: disable=too-many-branches, too-many-statements
        now = timezone.now()

        for source in DataSource.objects.all():
            last_alert = DataSourceAlert.objects.filter(data_source=source, generator_identifier=GENERATOR, active=True).order_by('-created').first()

            last_upload = DataPoint.objects.filter(source=source.identifier, generator_identifier=GENERATOR).order_by('-created').first()

            alert_name = None
            alert_details = {}
            alert_level = 'info'

            delta = now - last_upload.created

            if last_upload is not None:
                if delta.days >= WARNING_DAYS:
                    alert_name = 'Withings upload is overdue'
                    alert_details['message'] = 'Latest Withings upload was 1 day ago.'
                    alert_level = 'warning'

                elif delta.days >= CRITICAL_DAYS:
                    alert_name = 'Withings upload is critically overdue'
                    alert_details['message'] = 'Latest Withings upload was ' + str(delta.days) + ' days ago.'
                    alert_level = 'critical'

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
                alert_name = 'Withing data never uploaded'
                alert_details['message'] = 'No Withings data is available from this user.'

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

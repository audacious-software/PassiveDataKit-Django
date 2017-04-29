# pylint: disable=no-member,line-too-long

import datetime
import json

from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand
from django.utils import timezone

from ...decorators import handle_lock
from ...models import DataPoint, DataBundle, install_supports_jsonfield

class Command(BaseCommand):
    help = 'Convert unprocessed DataBundle instances into DataPoint instances.'

    def add_arguments(self, parser):
        parser.add_argument('--delete',
                            action='store_true',
                            dest='delete',
                            default=False,
                            help='Delete data bundles after processing')

        parser.add_argument('--count',
                            type=int,
                            dest='bundle_count',
                            default=100,
                            help='Number of bundles to process in a single run')

    @handle_lock
    def handle(self, *args, **options):
        to_delete = []

        for bundle in DataBundle.objects.filter(processed=False)[:options['bundle_count']]:
            if install_supports_jsonfield() is False:
                bundle.properties = json.loads(bundle.properties)

            for bundle_point in bundle.properties:
                if 'passive-data-metadata' in bundle_point:
                    point = DataPoint(recorded=timezone.now())
                    point.source = bundle_point['passive-data-metadata']['source']
                    point.generator = bundle_point['passive-data-metadata']['generator']

                    if 'generator-id' in bundle_point['passive-data-metadata']:
                        point.generator_identifier = bundle_point['passive-data-metadata']['generator-id']

                    if 'latitude' in bundle_point['passive-data-metadata'] and 'longitude' in bundle_point['passive-data-metadata']:
                        point.generated_at = GEOSGeometry('POINT(' + str(bundle_point['passive-data-metadata']['longitude']) + ' ' + str(bundle_point['passive-data-metadata']['latitude']) + ')')

                    point.created = datetime.datetime.fromtimestamp(bundle_point['passive-data-metadata']['timestamp'], tz=timezone.get_default_timezone())

                    if install_supports_jsonfield():
                        point.properties = bundle_point
                    else:
                        point.properties = json.dumps(bundle_point, indent=2)

                    point.fetch_secondary_identifier()

                    point.save()

            if install_supports_jsonfield() is False:
                bundle.properties = json.dumps(bundle.properties, indent=2)

            bundle.processed = True
            bundle.save()

            if options['delete']:
                to_delete.append(bundle)

        for bundle in to_delete:
            bundle.delete()

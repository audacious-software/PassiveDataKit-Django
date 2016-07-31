import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from passive_data_kit.decorators import handle_lock
from passive_data_kit.models import DataPoint, DataBundle

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
            for bundle_point in bundle.properties:
                point = DataPoint(recorded=timezone.now())
                point.source = bundle_point['passive-data-metadata']['source']
                point.generator = bundle_point['passive-data-metadata']['generator']
                
                if 'generator-id' in bundle_point['passive-data-metadata']:
                    point.generator_identifier = bundle_point['passive-data-metadata']['generator-id']
                
                point.created = datetime.datetime.fromtimestamp(bundle_point['passive-data-metadata']['timestamp'], tz=timezone.get_default_timezone())
                point.properties = bundle_point
                point.save()
                
            bundle.processed = True
            bundle.save()
            
            if options['delete']:
                to_delete.append(bundle)

        for bundle in to_delete:
            bundle.delete()

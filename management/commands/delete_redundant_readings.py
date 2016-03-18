import datetime
import json

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from django.utils import timezone

from passive_data_kit.decorators import handle_lock
from passive_data_kit.models import DataPoint, DataBundle

class Command(BaseCommand):
    help = 'Deletes identical DataPoint objects that may have been uploaded more than once.'

    def add_arguments(self, parser):
        pass
#        parser.add_argument('--delete',
#            action='store_true',
#            dest='delete',
#            default=False,
#            help='Delete data bundles after processing')
#
#        parser.add_argument('--count', 
#            type=int, 
#            dest='bundle_count',
#            default=100,
#            help='Number of bundles to process in a single run')
    
    @handle_lock
    def handle(self, *args, **options):
        to_delete = []
        
        matches = DataPoint.objects.order_by('source', 'generator_identifier', 'created').values('source', 'generator_identifier', 'created').annotate(Count('pk'))
        
        dupes = []
        
        for match in matches:
            if match['pk__count'] > 1:
                dupes.append(match)

        to_delete = []
        
        for dupe in dupes:
            dupe_objs = DataPoint.objects.filter(source=dupe['source'], generator=dupe['generator_identifier'], created=dupe['created']).order_by('pk')
            
            for dupe_obj in dupe_objs[1:]:
                if dupe_objs[0].properties == dupe_obj.properties:
                    print(str(dupe))
                    
                    to_delete.append(dupe_obj.pk)       
                    
                    if len(to_delete) % 500 == 0:
                        print('TO DELETE: ' + str(len(to_delete)))
                        
        for pk in to_delete:
            DataPoint.objects.get(pk=pk).delete()
            
        if len(to_delete) > 0:
            print('Deleted duplicates: ' + str(len(to_delete)))


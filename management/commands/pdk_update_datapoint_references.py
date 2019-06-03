# pylint: disable=no-member, line-too-long

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from ...decorators import handle_lock
from ...models import DataPoint, CACHED_GENERATOR_DEFINITIONS, CACHED_SOURCE_REFERENCES

PAGE_SIZE = 50000

class Command(BaseCommand):
    help = 'Populates generator and source references on data points missing that metadata by iterating through all points in reverse order of ingestion.'

    @handle_lock
    def handle(self, *args, **options):
        last_check = timezone.now()

        page = DataPoint.objects.all().order_by('-pk').first().pk

        while page > 0:
            with transaction.atomic():
                for point in DataPoint.objects.filter(pk__gt=(page - PAGE_SIZE), pk__lte=page):
                    reference = point.fetch_source_reference(skip_save=True)
                    definition = point.fetch_generator_definition(skip_save=True)
                    
                    point.save()

                    if (point.pk % 5000) == 0:
                        print str(point.pk) + ': ' + str(reference) + ' -- ' + str(definition) + ' -- ' + str(len(CACHED_GENERATOR_DEFINITIONS)) + ' -- ' + str(len(CACHED_SOURCE_REFERENCES))

            page = (page - PAGE_SIZE)
            now = timezone.now()

            print 'ELAPSED: ' + str((now - last_check).total_seconds())
            last_check = now

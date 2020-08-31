# pylint: disable=no-member,line-too-long

from django.core.management.base import BaseCommand

from ...decorators import handle_lock
from ...models import DataBundle

class Command(BaseCommand):
    help = 'Removes processed DataBundle instances ro reclaim disk space.'

    def add_arguments(self, parser):
        parser.add_argument('--count',
                            type=int,
                            dest='batch_count',
                            default=5000,
                            help='Number of bundles to process in a single loop before repeating')

    @handle_lock
    def handle(self, *args, **options): # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        total = DataBundle.objects.filter(processed=True).count()

        first_bundle = DataBundle.objects.filter(processed=True).order_by('pk').first()

        if first_bundle is not None:
            start = first_bundle.pk + options['batch_count']

            start = start - (start % options['batch_count'])

            deleted = 0

            bundles = DataBundle.objects.filter(processed=True, pk__lte=start)

            while bundles.count() > 0:
                print(str(deleted) + ' / ' + str(total) + ' [' + str(start) + ']')

                # deleted += bundles.delete()[0]

                deleted += bundles._raw_delete(bundles.db) # pylint: disable=protected-access

                start += options['batch_count']

                bundles = DataBundle.objects.filter(processed=True, pk__lte=start)

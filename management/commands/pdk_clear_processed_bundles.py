# pylint: disable=no-member,line-too-long
from __future__ import print_function

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

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

        pending_pks = DataBundle.objects.filter(processed=True).order_by('pk').values('pk')

        clear_index = 0
        total = len(pending_pks)

        # for pk in pending_pks:
        while clear_index < total:
            if (clear_index % 1000) == 0:
                logging.info('Progress: %s of %s (%s)', clear_index, total, timezone.now())

            # clear_index += 1
            clear_index += 5000

            # DataBundle.objects.get(pk=pk.get('pk', -1)).delete()
            to_delete = DataBundle.objects.filter(pk__gte=pending_pks[clear_index]['pk'], pk__lte=pending_pks[clear_index + 5000]['pk'])

            to_delete._raw_delete(to_delete.db)


#       first_bundle = DataBundle.objects.filter(processed=True).order_by('pk').only('pk').first()
#
#       if first_bundle is not None:
#           start = first_bundle.pk + options['batch_count']
#
#           start = start - (start % options['batch_count'])
#
#           deleted = 0
#
#           bundles = DataBundle.objects.filter(processed=True, pk__lte=start)
#
#           while bundles.count() > 0:
#               logging.debug('Progress: %s of %s (%s)', deleted, total, timezone.now())
#
#               deleted += bundles._raw_delete(bundles.db) # pylint: disable=protected-access
#
#               start += options['batch_count']
#
#               bundles = DataBundle.objects.filter(processed=True, pk__lte=start)
#

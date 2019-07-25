# pylint: disable=no-member,line-too-long

import datetime
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from ...decorators import handle_lock
from ...models import DataBundle

class Command(BaseCommand):
    help = 'Removes processed DataBundle instances.'

    def add_arguments(self, parser):
        parser.add_argument('--older-than-days',
                            type=int,
                            dest='age_days',
                            default=14,
                            help='Remove bundles older than this many days')

    @handle_lock
    def handle(self, *args, **options): # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        oldest = timezone.now() - datetime.timedelta(days=options['age_days'])

        removed = DataBundle.objects.filter(processed=True, recorded__lte=oldest).delete()

        logging.info("Removed %d unprocessed payloads.", removed)
        
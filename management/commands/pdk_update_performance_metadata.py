# pylint: disable=no-member

from django.core.management.base import BaseCommand

from ...decorators import handle_lock, log_scheduled_event
from ...models import DataSource

class Command(BaseCommand):
    help = 'Updates each user performance metadata measurements on a round-robin basis'

    def add_arguments(self, parser):
        parser.add_argument('--source',
                            type=str,
                            dest='source',
                            default='any',
                            help='Specific source to update')

    @handle_lock
    @log_scheduled_event
    def handle(self, *args, **options):
        source = None

        if options['source'] != 'any':
            source = DataSource.objects.filter(identifier=options['source']).first()

        if source is None:
            source = DataSource.objects.filter(performance_metadata_updated=None).first()

        if source is None:
            source = DataSource.objects.all().order_by('performance_metadata_updated').first()

        if source is not None:
            source.update_performance_metadata()

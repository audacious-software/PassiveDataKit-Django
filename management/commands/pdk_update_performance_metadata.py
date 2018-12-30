# pylint: disable=no-member

from django.core.management.base import BaseCommand

from ...decorators import handle_lock
from ...models import DataSource

class Command(BaseCommand):
    help = 'Updates each user performance metadata measurements on a round-robin basis'

    @handle_lock
    def handle(self, *args, **options):
        source = DataSource.objects.filter(performance_metadata_updated=None).first()
        
        if source is None:
            source = DataSource.objects.all().order_by('performance_metadata_updated').first()

        if source is not None:
            source.update_performance_metadata()

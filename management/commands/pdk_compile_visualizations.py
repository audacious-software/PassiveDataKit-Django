# pylint: disable=no-member,line-too-long

import datetime
import importlib
import os

import pytz

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from passive_data_kit.decorators import handle_lock
from passive_data_kit.models import DataPoint, DataPointVisualizations

class Command(BaseCommand):
    help = 'Compiles support files and other resources used for data inspection and visualization.'

    def add_arguments(self, parser):
        parser.add_argument('--source',
                            type=str,
                            dest='source',
                            default='all',
                            help='Specific source to regenerate')

    @handle_lock
    def handle(self, *args, **options): # pylint: disable=too-many-branches
        last_updated = None

        sources = []

        if options['source'] != 'all':
            sources = [options['source']]
        else:
            sources = sorted(DataPoint.objects.sources())

        for source in sources:
            identifiers = DataPoint.objects.generator_identifiers_for_source(source)

            for identifier in identifiers:
                compiled = DataPointVisualizations.objects.filter(source=source, generator_identifier=identifier).order_by('last_updated').first()

                if compiled is None:
                    compiled = DataPointVisualizations(source=source, generator_identifier=identifier)

                    compiled.last_updated = pytz.timezone('UTC').localize(datetime.datetime.min)
                    compiled.save()

                last_point = DataPoint.objects.filter(source=source, generator_identifier=identifier).order_by('-recorded').first()

                if last_point is not None and last_point.recorded > compiled.last_updated:
                    if last_updated is None:
                        last_updated = compiled
                    elif last_updated.last_updated > compiled.last_updated:
                        last_updated = compiled

        if last_updated is not None:
            points = DataPoint.objects.filter(source=last_updated.source, generator_identifier=last_updated.generator_identifier)

            folder = settings.MEDIA_ROOT + '/pdk_visualizations/' + last_updated.source + '/' + last_updated.generator_identifier

            if os.path.exists(folder) is False:
                os.makedirs(folder)

            for app in settings.INSTALLED_APPS:
                try:
                    pdk_api = importlib.import_module(app + '.pdk_api')

                    pdk_api.compile_visualization(last_updated.generator_identifier, points, folder)
                except ImportError:
                    pass
                except AttributeError:
                    pass

            last_updated.last_updated = timezone.now()
            last_updated.save()

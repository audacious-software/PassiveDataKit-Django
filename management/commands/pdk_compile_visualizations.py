# pylint: disable=no-member,line-too-long

import datetime
import importlib
import os

import pytz

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from passive_data_kit.decorators import handle_lock
from passive_data_kit.models import DataPoint, DataPointVisualization, DataSource

class Command(BaseCommand):
    help = 'Compiles support files and other resources used for data inspection and visualization.'

    def add_arguments(self, parser):
        parser.add_argument('--source',
                            type=str,
                            dest='source',
                            default='all',
                            help='Specific source to regenerate')

        parser.add_argument('--repeat',
                            type=int,
                            dest='repeat',
                            default=10,
                            help='Number of times to repeat in a single run')

    @handle_lock
    def handle(self, *args, **options): # pylint: disable=too-many-branches, too-many-locals
        repeat = options['repeat']

        while repeat > 0:
            last_updated = None

            sources = []

            if options['source'] != 'all':
                sources = [options['source']]
            else:
                sources = sorted(DataSource.objects.sources())

#            print('LOOP[' + str(repeat) + '] = ' + str(len(sources)))

            update_delta = 0

            for source in sources:
                identifier_list = ['pdk-data-frequency']

                for identifier in DataPoint.objects.generator_identifiers_for_source(source):
                    identifier_list.append(identifier)

                for identifier in identifier_list:
#                    print(timezone.now().isoformat() + ' -- ' + source + ' -- ' + identifier)

                    compiled = DataPointVisualization.objects.filter(source=source, generator_identifier=identifier).order_by('last_updated').first()

                    if compiled is None:
                        compiled = DataPointVisualization(source=source, generator_identifier=identifier)

                        compiled.last_updated = pytz.timezone('UTC').localize(datetime.datetime.min)
                        compiled.save()

                    last_point = DataPoint.objects.latest_point(source, identifier)

                    if last_point is not None:
                        this_delta = (last_point.recorded - compiled.last_updated).total_seconds()

                        if this_delta > update_delta:
                            last_updated = compiled
                            update_delta = this_delta

            if last_updated is not None:
#                print('UPDATING: ' + last_updated.source + ' -- ' + last_updated.generator_identifier)

                points = None

                if last_updated.generator_identifier == 'pdk-data-frequency':
                    points = DataPoint.objects.filter(source=last_updated.source)
                else:
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
                    except NotImplementedError:
                        pass

                last_updated.last_updated = timezone.now()
                last_updated.save()
            else:
                repeat = 0

            repeat -= 1

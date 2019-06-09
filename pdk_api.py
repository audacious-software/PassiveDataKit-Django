# pylint: disable=line-too-long, no-member

import calendar
import csv
import importlib
import json
import os
import tempfile
import traceback

import dropbox

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from .models import DataPoint

# def name_for_generator(identifier):
#    if identifier == 'web-historian':
#        return 'Web Historian Web Visits'
#
#    return None

# def compile_visualization(identifier, points_query, folder):
#
#    if identifier == 'web-historian':
#

def visualization(source, generator):
    try:
        generator_module = importlib.import_module('.generators.' + generator.replace('-', '_'), package='passive_data_kit')

        output = generator_module.visualization(source, generator)

        if output is not None:
            return output
    except ImportError:
        # traceback.print_exc()
        pass
    except AttributeError:
        # traceback.print_exc()
        pass

    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    rows = []

    for point in DataPoint.objects.filter(source=source.identifier, generator_identifier=generator).order_by('-created')[:1000]:
        row = {}

        row['created'] = point.created
        row['value'] = '-'

        rows.append(row)

    context['table_rows'] = rows

    return render_to_string('pdk_generic_viz_template.html', context)

def data_table(source, generator):
    for app in settings.INSTALLED_APPS:
        try:
            generator_module = importlib.import_module('.generators.' + generator.replace('-', '_'), package=app)

            output = generator_module.data_table(source, generator)

            if output is not None:
                return output
        except ImportError:
            pass
        except AttributeError:
            pass

    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    rows = []

    for point in DataPoint.objects.filter(source=source.identifier, generator_identifier=generator).order_by('-created')[:1000]:
        row = {}

        row['created'] = point.created
        row['value'] = '-'

        rows.append(row)

    context['table_rows'] = rows

    return render_to_string('pdk_generic_viz_template.html', context)

def compile_report(generator, sources, data_start=None, data_end=None, date_type='created'): # pylint: disable=too-many-locals
    try:
        generator_module = importlib.import_module('.generators.' + generator.replace('-', '_'), package='passive_data_kit')

        output_file = None

        try:
            output_file = generator_module.compile_report(generator, sources, data_start=data_start, data_end=data_end, date_type=date_type)
        except TypeError:
            print 'TODO: Update ' + generator + '.compile_report to support data_start, data_end, and date_type parameters!'

            output_file = generator_module.compile_report(generator, sources)

        if output_file is not None:
            return output_file
    except ImportError:
        pass
    except AttributeError:
        pass

    filename = tempfile.gettempdir() + '/' + generator + '.txt'

    with open(filename, 'w') as outfile:
        writer = csv.writer(outfile, delimiter='\t')

        writer.writerow([
            'Source',
            'Generator',
            'Generator Identifier',
            'Created Timestamp',
            'Created Date',
            'Latitude',
            'Longitude',
            'Recorded Timestamp',
            'Recorded Date',
            'Properties'
        ])

        for source in sources:
            points = DataPoint.objects.filter(source=source, generator_identifier=generator).order_by('created') # pylint: disable=no-member,line-too-long

            index = 0
            count = points.count()

            while index < count:
                for point in points[index:(index + 5000)]:
                    row = []

                    row.append(point.source)
                    row.append(point.generator)
                    row.append(point.generator_identifier)
                    row.append(calendar.timegm(point.created.utctimetuple()))
                    row.append(point.created.isoformat())

                    if point.generated_at is not None:
                        row.append(point.generated_at.y)
                        row.append(point.generated_at.x)
                    else:
                        row.append('')
                        row.append('')

                    row.append(calendar.timegm(point.recorded.utctimetuple()))
                    row.append(point.recorded.isoformat())
                    row.append(json.dumps(point.properties))

                    writer.writerow(row)

                index += 5000

    return filename

def compile_visualization(identifier, points, folder):
    try:
        generator_module = importlib.import_module('.generators.' + identifier.replace('-', '_'), package='passive_data_kit')

        generator_module.compile_visualization(identifier, points, folder)
    except ImportError:
        pass
    except AttributeError:
        pass

def extract_location_method(identifier):
    try:
        generator_module = importlib.import_module('.generators.' + identifier.replace('-', '_'), package='passive_data_kit')

        return generator_module.extract_location
    except ImportError:
        pass
    except AttributeError:
        pass

    return None

def send_to_destination(destination, report_path):
    file_sent = False

    if destination.destination == 'dropbox':
        try:
            parameters = destination.fetch_parameters()

            if 'access_token' in parameters:
                client = dropbox.Dropbox(parameters['access_token'])

                path = '/'

                if 'path' in parameters:
                    path = parameters['path']

                path = path + '/'

                if 'prepend_date' in parameters:
                    path = path + timezone.now().date().isoformat() + '-'

                path = path + os.path.basename(os.path.normpath(report_path))

                with open(report_path, 'rb') as report_file:
                    client.files_upload(report_file.read(), path)

                file_sent = True
        except BaseException:
            traceback.print_exc()

    if file_sent is False:
        print 'Unable to transmit report to destination "' + destination.destination + '".'

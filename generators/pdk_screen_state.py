from __future__ import division
# pylint: disable=line-too-long, no-member

from builtins import str
from past.utils import old_div
import calendar
import csv
import datetime
import json
import os
import tempfile

from zipfile import ZipFile

import arrow
import pytz

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify

from ..models import DataPoint, DataSourceReference, DataGeneratorDefinition

def generator_name(identifier): # pylint: disable=unused-argument
    return 'Screen State'

def visualization(source, generator):
    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    now = timezone.now()

    days = []

    start = datetime.datetime(now.year, now.month, now.day, 0, 0, 0, 0, pytz.timezone(settings.TIME_ZONE))

    while len(days) < 7:
        end = start + datetime.timedelta(days=1)

        points = DataPoint.objects.filter(source=source.identifier, generator_identifier=generator, created__gt=start, created__lte=end).order_by('created')

        point_list = []

        for point in points:
            properties = point.fetch_properties()

            data_obj = {
                'timestamp': calendar.timegm(point.created.utctimetuple()),
                'value': properties['state']
            }

            point_list.append(data_obj)

        day = {
            'points': point_list,
            'start_txt': start.isoformat(),
            'start': calendar.timegm(start.utctimetuple()),
            'end': calendar.timegm(end.utctimetuple())
        }

        days.insert(0, day)

        start = start - datetime.timedelta(days=1)

    context['days'] = json.dumps(days)

    return render_to_string('pdk_device_screen_state_template.html', context)

def data_table(source, generator):
    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    context['values'] = DataPoint.objects.filter(source=source.identifier, generator_identifier=generator).order_by('-created')[:1000]

    return render_to_string('pdk_screen_state_table_template.html', context)

def compile_report(generator, sources, data_start=None, data_end=None, date_type='created'): # pylint: disable=too-many-locals
    now = arrow.get()
    filename = tempfile.gettempdir() + '/pdk_export_' + str(now.timestamp) + str(old_div(now.microsecond, 1e6)) + '.zip'

    with ZipFile(filename, 'w') as export_file:
        seen_sources = []

        for source in sources:
            export_source = source

            seen_index = 1

            while slugify(export_source) in seen_sources:
                export_source = source + '__' + str(seen_index)

                seen_index += 1

            seen_sources.append(slugify(export_source))

            identifier = slugify(generator + '__' + export_source)

            secondary_filename = tempfile.gettempdir() + '/' + identifier + '.txt'

            with open(secondary_filename, 'w') as outfile:
                writer = csv.writer(outfile, delimiter='\t')

                columns = [
                    'Source',
                    'Created Timestamp',
                    'Created Date',
                    'Recorded Timestamp',
                    'Recorded Date',
                    'Screen State'
                ]

                writer.writerow(columns)

                source_reference = DataSourceReference.reference_for_source(source)
                generator_definition = DataGeneratorDefinition.definition_for_identifier(generator)

                points = DataPoint.objects.filter(source_reference=source_reference, generator_definition=generator_definition)

                if data_start is not None:
                    if date_type == 'recorded':
                        points = points.filter(recorded__gte=data_start)
                    else:
                        points = points.filter(created__gte=data_start)

                if data_end is not None:
                    if date_type == 'recorded':
                        points = points.filter(recorded__lte=data_end)
                    else:
                        points = points.filter(created__lte=data_end)

                points = points.order_by('source', 'created')

                for point in points:
                    properties = point.fetch_properties()

                    row = []

                    created = point.created.astimezone(pytz.timezone(settings.TIME_ZONE))
                    recorded = point.recorded.astimezone(pytz.timezone(settings.TIME_ZONE))

                    row.append(point.source)
                    row.append(calendar.timegm(point.created.utctimetuple()))
                    row.append(created.isoformat())
                    row.append(calendar.timegm(point.recorded.utctimetuple()))
                    row.append(recorded.isoformat())

                    row.append(properties['state'])

                    writer.writerow(row)

            export_file.write(secondary_filename, slugify(generator) + '/' + slugify(export_source) + '.txt')

            os.remove(secondary_filename)

    return filename

def extract_secondary_identifier(properties):
    if 'state' in properties:
        return properties['state']

    return None

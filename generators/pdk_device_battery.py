# pylint: disable=line-too-long, no-member

from __future__ import division

from builtins import str # pylint: disable=redefined-builtin

import csv
import calendar
import datetime
import json
import os
import tempfile

from zipfile import ZipFile

from past.utils import old_div

import arrow
import pytz

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.text import slugify

from ..models import DataPoint, DataSourceReference, DataGeneratorDefinition

def extract_secondary_identifier(properties):
    if 'status' in properties:
        return properties['status']

    return None

def generator_name(identifier): # pylint: disable=unused-argument
    return 'Device Battery Status'

def visualization(source, generator): # pylint: disable=unused-argument
    context = {}

    filename = settings.MEDIA_ROOT + os.path.sep + 'pdk_visualizations' + os.path.sep + source.identifier + os.path.sep + 'pdk-device-battery' + os.path.sep + 'battery-level.json'

    with open(filename) as infile:
        context['data'] = json.load(infile)

    filename = settings.MEDIA_ROOT + os.path.sep + 'pdk_visualizations' + os.path.sep + source.identifier + os.path.sep + 'pdk-device-battery' + os.path.sep + 'timestamp-counts.json'

    try:
        with open(filename) as infile:
            hz_data = json.load(infile)

            context['hz_data'] = hz_data
    except IOError:
        context['hz_data'] = {}

    return render_to_string('generators/pdk_device_battery_template.html', context)

def compile_visualization(identifier, points, folder): # pylint: disable=unused-argument
    context = {}

    values = []

    latest = points.order_by('-created').first()

    now = latest.created.replace(second=0, microsecond=0)

    remainder = 10 - (now.minute % 10)

    now = now.replace(minute=((now.minute + remainder) % 60))

    start = now - datetime.timedelta(days=7)

    for point in points.filter(created__gte=start).order_by('created'):
        properties = point.fetch_properties()

        value = {}

        value['ts'] = properties['passive-data-metadata']['timestamp']
        value['value'] = properties['level']

        values.append(value)

    context['values'] = values

    context['start'] = calendar.timegm(start.timetuple())
    context['end'] = calendar.timegm(now.timetuple())

    with open(folder + os.path.sep + 'battery-level.json', 'w') as outfile:
        json.dump(context, outfile, indent=2)

    compile_frequency_visualization(identifier, points, folder)

def compile_frequency_visualization(identifier, points, folder): # pylint: disable=unused-argument
    latest = points.order_by('-created').first()

    now = latest.created.replace(second=0, microsecond=0)

    remainder = 10 - (now.minute % 10)

    now = now.replace(minute=((now.minute + remainder) % 60))

    start = now - datetime.timedelta(days=7)

    points = points.filter(created__lte=now, created__gte=start).order_by('created')

    end = start + datetime.timedelta(seconds=600)
    point_index = 0
    point_count = points.count()

    point = None

    if point_count > 0:
        point = points[point_index]

    timestamp_counts = {}

    keys = []

    while start < now:
        timestamp = str(calendar.timegm(start.timetuple()))

        keys.append(timestamp)

        timestamp_counts[timestamp] = 0

        while point is not None and point.created < end and point_index < (point_count - 1):
            timestamp_counts[timestamp] += 1

            point_index += 1

            point = points[point_index]

        start = end
        end = start + datetime.timedelta(seconds=600)

    timestamp_counts['keys'] = keys

    with open(folder + os.path.sep + 'timestamp-counts.json', 'w') as outfile:
        json.dump(timestamp_counts, outfile, indent=2)

def data_table(source, generator):
    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    point_count = 1000

    try:
        point_count = settings.PDK_LOGGED_VALUES_COUNT
    except AttributeError:
        pass

    context['values'] = DataPoint.objects.filter(source=source.identifier, generator_identifier=generator).order_by('-created')[:point_count]

    return render_to_string('generators/pdk_device_battery_table_template.html', context)


def compile_report(generator, sources, data_start=None, data_end=None, date_type='created'): # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    now = arrow.get()
    filename = tempfile.gettempdir() + os.path.sep + 'pdk_export_' + str(now.timestamp) + str(old_div(now.microsecond, 1e6)) + '.zip'

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

            secondary_filename = tempfile.gettempdir() + os.path.sep + identifier + '.txt'

            with open(secondary_filename, 'w') as outfile:
                writer = csv.writer(outfile, delimiter='\t')

                columns = [
                    'Source',
                    'Created Timestamp',
                    'Created Date',
                    'Recorded Timestamp',
                    'Recorded Date',
                    'Level',
                    'Scale',
                    'Plugged',
                    'Health',
                    'Voltage',
                    'Technology',
                    'Present',
                    'Temperature',
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

                    row.append(properties['level'])

                    if 'scale' in properties:
                        row.append(properties['scale'])
                    else:
                        row.append('')

                    if 'plugged' in properties:
                        row.append(properties['plugged'])
                    else:
                        row.append('')

                    if 'health' in properties:
                        row.append(properties['health'])
                    else:
                        row.append('')

                    if 'voltage' in properties:
                        row.append(properties['voltage'])
                    else:
                        row.append('')

                    if 'technology' in properties:
                        row.append(properties['technology'])
                    else:
                        row.append('')

                    if 'present' in properties:
                        row.append(properties['present'])
                    else:
                        row.append('')

                    if 'temperature' in properties:
                        row.append(properties['temperature'])
                    else:
                        row.append('')

                    writer.writerow(row)

            export_file.write(secondary_filename, slugify(generator) + '/' + slugify(export_source) + '.txt')

            os.remove(secondary_filename)

    return filename

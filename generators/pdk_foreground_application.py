# pylint: disable=line-too-long, no-member

import calendar
import csv
import datetime
import json
import os
import tempfile
import time

from zipfile import ZipFile

import arrow
import pytz

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify

from ..models import DataPoint

def extract_secondary_identifier(properties):
    if 'application' in properties:
        return properties['application']

    return None

def generator_name(identifier): # pylint: disable=unused-argument
    return 'Foreground Application'

def visualization(source, generator):
    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    filename = settings.MEDIA_ROOT + '/pdk_visualizations/' + source.identifier + '/pdk-foreground-application/timestamp-counts.json'

    try:
        with open(filename) as infile:
            hz_data = json.load(infile)

            context['hz_data'] = hz_data
    except IOError:
        context['hz_data'] = {}

    return render_to_string('generators/pdk_foreground_application_template.html', context)

def compile_visualization(identifier, points, folder): # pylint: disable=unused-argument
    now = timezone.now()

    now = now.replace(second=0, microsecond=0)

    remainder = now.minute % 10

    now = now.replace(minute=(now.minute - remainder))

    start = now - datetime.timedelta(days=2)

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
        timestamp = str(time.mktime(start.timetuple()))

        keys.append(timestamp)

        timestamp_counts[timestamp] = 0

        while point is not None and point.created < end and point_index < (point_count - 1):
            timestamp_counts[timestamp] += 1

            point_index += 1

            point = points[point_index]

        start = end
        end = start + datetime.timedelta(seconds=600)

    timestamp_counts['keys'] = keys

    with open(folder + '/timestamp-counts.json', 'w') as outfile:
        json.dump(timestamp_counts, outfile, indent=2)

def data_table(source, generator): # pylint: disable=too-many-locals
    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    end = timezone.now()
    start = end - datetime.timedelta(days=1)

    values = []

    last_active = None
    last_application = None
    last_start = None
    cumulative_duration = 0

    for point in DataPoint.objects.filter(source=source.identifier, generator_identifier=generator, created__gt=start, created__lte=end).order_by('created'):
        properties = point.fetch_properties()

        active = None

        if 'screen_active' in properties:
            active = properties['screen_active']

        application = None

        if 'application' in properties:
            application = properties['application']

        update = False

        if active != last_active:
            update = True

        if application != last_application:
            update = True

        if update:
            if last_start != None:
                value = {
                    'screen_active': last_active,
                    'application': last_application,
                    'start': last_start,
                    'duration': datetime.timedelta(seconds=(cumulative_duration / 1000))
                }

                values.append(value)

            last_active = active
            last_application = application
            last_start = point.created
            cumulative_duration = 0
        else:
            cumulative_duration += properties['duration']

    context['values'] = values

    return render_to_string('pdk_foreground_application_table_template.html', context)

def compile_report(generator, sources, data_start=None, data_end=None): # pylint: disable=too-many-locals
    now = arrow.get()
    filename = tempfile.gettempdir() + '/pdk_export_' + str(now.timestamp) + str(now.microsecond / 1e6) + '.zip'

    with ZipFile(filename, 'w') as export_file:
        for source in sources:
            identifier = slugify(generator + '__' + source)

            secondary_filename = tempfile.gettempdir() + '/' + identifier + '.txt'

            with open(secondary_filename, 'w') as outfile:
                writer = csv.writer(outfile, delimiter='\t')

                columns = [
                    'Source',
                    'Created Timestamp',
                    'Created Date',
                    'Application',
                    'Duration',
                    'Screen Active',
                ]

                writer.writerow(columns)

                points = DataPoint.objects.filter(source=source, generator_identifier=generator)

                if data_start is not None:
                    points = points.filter(created__gte=data_start)

                if data_end is not None:
                    points = points.filter(created__lte=data_end)

                points = points.order_by('source', 'created')

                for point in points:
                    properties = point.fetch_properties()

                    row = []

                    created = point.created.astimezone(pytz.timezone(settings.TIME_ZONE))

                    row.append(point.source)
                    row.append(calendar.timegm(point.created.utctimetuple()))
                    row.append(created.isoformat())

                    properties = point.fetch_properties()

                    if 'application' in properties:
                        row.append(properties['application'])
                    else:
                        row.append('')

                    if 'duration' in properties:
                        row.append(str(properties['duration']))
                    else:
                        row.append('')

                    if 'screen_active' in properties:
                        row.append(str(properties['screen_active']))
                    else:
                        row.append('')

                    writer.writerow(row)

            export_file.write(secondary_filename, slugify(generator) + '/' + slugify(source) + '.txt')

            os.remove(secondary_filename)

    return filename

from __future__ import division
# pylint: disable=line-too-long, no-member

from builtins import str
from past.utils import old_div
import calendar
import csv
import datetime
import json
import tempfile
import time

import pytz

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from ..models import DataPoint, DataSourceReference, DataGeneratorDefinition

def generator_name(identifier): # pylint: disable=unused-argument
    return 'Text Messages'

def extract_secondary_identifier(properties):
    if 'direction' in properties:
        return properties['direction']

    return None

def compile_report(generator, sources, data_start=None, data_end=None, date_type='created'): # pylint: disable=too-many-locals
    filename = tempfile.gettempdir() + '/pdk_' + generator + '.txt'

    default_tz = timezone.get_default_timezone()

    with open(filename, 'w') as outfile:
        writer = csv.writer(outfile, delimiter='\t')

        writer.writerow([
            'Source',
            'Created Timestamp',
            'Created Date',
            'Recorded Timestamp',
            'Recorded Date',
            'Direction',
            'Person',
            'Address',
            'Length',
            'Body',
        ])

        for source in sources:
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

            index = 0
            count = points.count()

            while index < count:
                for point in points[index:(index + 5000)]:
                    properties = point.fetch_properties()

                    point_tz = pytz.timezone(settings.TIME_ZONE)

                    if 'timezone' in properties['passive-data-metadata']:
                        point_tz = pytz.timezone(properties['passive-data-metadata']['timezone'])

                    created = datetime.datetime.fromtimestamp(old_div(properties['date'], 1000), tz=default_tz)

                    row = []

                    created = created.astimezone(point_tz)
                    recorded = point.recorded.astimezone(point_tz)

                    row.append(point.source)
                    row.append(calendar.timegm(created.utctimetuple()))
                    row.append(created.isoformat())

                    row.append(calendar.timegm(point.recorded.utctimetuple()))
                    row.append(recorded.isoformat())

                    row.append(properties['direction'])
                    row.append(properties['person'])
                    row.append(properties['address'])
                    row.append(properties['length'])
                    row.append(properties['body'])

                    writer.writerow(row)

                index += 5000

    return filename

def data_table(source, generator):
    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    source_reference = DataSourceReference.reference_for_source(source.identifier)
    generator_definition = DataGeneratorDefinition.definition_for_identifier(generator)

    context['values'] = DataPoint.objects.filter(source_reference=source_reference, generator_definition=generator_definition).order_by('created')

    return render_to_string('pdk_text_messages_table_template.html', context)

def visualization(source, generator): # pylint: disable=unused-argument
    filename = settings.MEDIA_ROOT + '/pdk_visualizations/' + source.identifier + '/pdk-text-messages/timestamp-counts.json'

    with open(filename) as infile:
        data = json.load(infile)

        context = {}

        context['data'] = data

        return render_to_string('pdk_text_messages_viz_template.html', context)

    return None

def compile_visualization(identifier, points, folder): # pylint: disable=unused-argument
    now = timezone.now()

    now = now.replace(minute=0, second=0, microsecond=0)

    start = now - datetime.timedelta(days=30)

    points = points.filter(created__lte=now, created__gte=start).order_by('created')

    end = start + datetime.timedelta(hours=1)
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
        end = start + datetime.timedelta(hours=1)

    timestamp_counts['keys'] = keys

    with open(folder + '/timestamp-counts.json', 'w') as outfile:
        json.dump(timestamp_counts, outfile, indent=2)

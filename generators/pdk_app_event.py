# pylint: disable=line-too-long, no-member

import calendar
import csv
import datetime
import json
import tempfile
import time

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from ..models import DataPoint, install_supports_jsonfield

def generator_name(identifier): # pylint: disable=unused-argument
    return 'App Events'

def extract_secondary_identifier(properties):
    if 'event_name' in properties:
        return properties['event_name']

    return None

def compile_report(generator, sources):
    filename = tempfile.gettempdir() + '/pdk_' + generator + '.txt'

    with open(filename, 'w') as outfile:
        writer = csv.writer(outfile, delimiter='\t')

        writer.writerow([
            'Source',
            'Created Timestamp',
            'Created Date',
            'Event Name',
            'Event Properties'
        ])

        for source in sources:
            points = DataPoint.objects.filter(source=source, generator_identifier=generator).order_by('created') # pylint: disable=no-member,line-too-long

            index = 0
            count = points.count()

            while index < count:
                for point in points[index:(index + 5000)]:
                    row = []

                    row.append(point.source)
                    row.append(calendar.timegm(point.created.utctimetuple()))
                    row.append(point.created.isoformat())

                    properties = {}

                    if install_supports_jsonfield():
                        properties = point.properties
                    else:
                        properties = json.loads(point.properties)

                    row.append(properties['event_name'])
                    row.append(json.dumps(properties['event_details']))

                    writer.writerow(row)

                index += 5000

    return filename

def data_table(source, generator):
    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    end = timezone.now()
    start = end - datetime.timedelta(days=30)

    context['values'] = DataPoint.objects.filter(source=source.identifier, generator_identifier=generator, created__gt=start, created__lte=end).order_by('created')

    return render_to_string('pdk_app_event_table_template.html', context)

def visualization(source, generator): # pylint: disable=unused-argument
    filename = settings.MEDIA_ROOT + '/pdk_visualizations/' + source.identifier + '/pdk-app-event/timestamp-counts.json'

    with open(filename) as infile:
        data = json.load(infile)

        context = {}

        context['data'] = data

        return render_to_string('pdk_app_event_viz_template.html', context)

    return None

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

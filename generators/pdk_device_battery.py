# pylint: disable=line-too-long, no-member

import datetime
import json
import time

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from ..models import DataPoint

def extract_secondary_identifier(properties):
    if 'status' in properties:
        return properties['status']

    return None

def generator_name(identifier): # pylint: disable=unused-argument
    return 'Device Battery Status'

def visualization(source, generator): # pylint: disable=unused-argument
    context = {}

    filename = settings.MEDIA_ROOT + 'pdk_visualizations/' + source.identifier + '/pdk-device-battery/battery-level.json'

    with open(filename) as infile:
        context['data'] = json.load(infile)

    filename = settings.MEDIA_ROOT + '/pdk_visualizations/' + source.identifier + '/pdk-device-battery/timestamp-counts.json'

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

    now = timezone.now()

    now = now.replace(second=0, microsecond=0)

    remainder = now.minute % 10

    now = now.replace(minute=(now.minute - remainder))

    start = now - datetime.timedelta(days=2)

    for point in points.filter(created__gte=start).order_by('created'):
        properties = point.fetch_properties()

        value = {}

        value['ts'] = properties['passive-data-metadata']['timestamp']
        value['value'] = properties['level']

        values.append(value)

    context['values'] = values

    context['start'] = time.mktime(start.timetuple())
    context['end'] = time.mktime(now.timetuple())

    with open(folder + '/battery-level.json', 'w') as outfile:
        json.dump(context, outfile, indent=2)

    compile_frequency_visualization(identifier, points, folder)

def compile_frequency_visualization(identifier, points, folder): # pylint: disable=unused-argument
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


# def compile_report(generator, sources): # pylint: disable=too-many-locals
#    timestamp = arrow.get()
#    filename = tempfile.gettempdir() + '/pdk_export_' + str(timestamp.seconds) + '.' + \
#               str(timestamp.seconds / 1e6) + '.zip'
#
#    with ZipFile(filename, 'w') as export_file:
#        for secondary_identifier in SECONDARY_FIELDS:
#            secondary_filename = tempfile.gettempdir() + '/' + generator + '-' + \
#                                 secondary_identifier + '.txt'
#
#            with open(secondary_filename, 'w') as outfile:
#                writer = csv.writer(outfile, delimiter='\t')
#
#                columns = [
#                    'Source',
#                    'Created Timestamp',
#                    'Created Date',
#                ]
#
#                for column in SECONDARY_FIELDS[secondary_identifier]:
#                    columns.append(column)
#
#                writer.writerow(columns)
#
#                for source in sources:
#                    points = DataPoint.objects.filter(source=source, generator_identifier=generator, secondary_identifier=secondary_identifier).order_by('source', 'created') # pylint: disable=no-member,line-too-long
#
#                    index = 0
#                    count = points.count()
#
#                    while index < count:
#                        for point in points[index:(index + 5000)]:
#                            row = []
#
#                            row.append(point.source)
#                            row.append(calendar.timegm(point.created.utctimetuple()))
#                            row.append(point.created.isoformat())
#
#                            properties = point.fetch_properties()
#
#                            for column in SECONDARY_FIELDS[secondary_identifier]:
#                                if column in properties:
#                                    row.append(properties[column])
#                                else:
#                                    row.append('')
#
#                            writer.writerow(row)
#
#                        index += 5000
#
#            export_file.write(secondary_filename, secondary_filename.split('/')[-1])
#
#    return filename

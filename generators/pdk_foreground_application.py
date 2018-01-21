# pylint: disable=line-too-long, no-member

import datetime
import json
import time

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

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

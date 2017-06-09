# pylint: disable=line-too-long, no-member

import datetime
import time

from django.template.loader import render_to_string
from django.utils import timezone

from ..models import DataPoint

WINDOW_SIZE = 300

def fetch_values(source, generator, start, end):
    values = []

    index = start
    current_value = None

    for point in DataPoint.objects.filter(source=source.identifier, generator_identifier=generator, created__gt=start, created__lte=end).order_by('created'):
        if (point.created - index).total_seconds() > WINDOW_SIZE:
            if current_value is not None and current_value['min_value'] != -1: # pylint: disable=unsubscriptable-object
                values.append(current_value)

            current_value = None
            index = index + datetime.timedelta(seconds=WINDOW_SIZE)

        if current_value is None:
            current_value = {
                'min_value': -1,
                'max_value': -1,
                'timestamp': time.mktime(index.timetuple()),
                'created': index,
                'duration': WINDOW_SIZE
            }

        properties = point.fetch_properties()

        for level in properties['sensor_data']['light_level']:
            if current_value['min_value'] == -1 or level < current_value['min_value']:
                current_value['min_value'] = level

            if current_value['max_value'] == -1 or level > current_value['max_value']:
                current_value['max_value'] = level

#        duration = properties['sensor_data']['observed'][-1] - properties['sensor_data']['observed'][0]
#        timestamp = properties['sensor_data']['observed'][0] + (duration / 2)
#
#        value['min_value'] = min_value
#        value['max_value'] = max_value
#        value['duration'] = duration / (1000 * 1000 * 1000)
#        value['timestamp'] = timestamp / (1000 * 1000 * 1000)
#        value['created'] = point.created
#
#        values.append(value)

    return values


def generator_name(identifier): # pylint: disable=unused-argument
    return 'Light Sensor'

def visualization(source, generator):
    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    end = timezone.now()
    start = end - datetime.timedelta(days=1)

    context['values'] = fetch_values(source, generator, start, end)

    context['start'] = time.mktime(start.timetuple())
    context['end'] = time.mktime(end.timetuple())

    return render_to_string('pdk_sensor_light_template.html', context)

def data_table(source, generator):
    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    end = timezone.now()
    start = end - datetime.timedelta(days=1)

    context['values'] = fetch_values(source, generator, start, end)

    return render_to_string('pdk_sensor_light_table_template.html', context)

# def compile_report(generator, sources): # pylint: disable=too-many-locals
#    filename = tempfile.gettempdir() + '/pdk_export_' + str(arrow.get().timestamp) + '.zip'
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

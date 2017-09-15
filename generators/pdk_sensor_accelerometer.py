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
import numpy

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify

from ..models import DataPoint

WINDOW_SIZE = 300

def generator_name(identifier): # pylint: disable=unused-argument
    return 'Accelerometer Sensor'

def compile_visualization(identifier, points, folder): # pylint: disable=unused-argument
    context = {}

    values = []

    end = timezone.now()
    start = end - datetime.timedelta(days=2)

    for point in points.filter(created__gte=start).order_by('created'):
        properties = point.fetch_properties()

        if 'sensor_data' in properties:
            value = {}

            value['ts'] = properties['passive-data-metadata']['timestamp']
            value['x_mean'] = numpy.mean(properties['sensor_data']['x'])
            value['y_mean'] = numpy.mean(properties['sensor_data']['y'])
            value['z_mean'] = numpy.mean(properties['sensor_data']['z'])

            value['x_std'] = numpy.std(properties['sensor_data']['x'])
            value['y_std'] = numpy.std(properties['sensor_data']['y'])
            value['z_std'] = numpy.std(properties['sensor_data']['z'])

            values.append(value)

    context['values'] = values

    context['start'] = time.mktime(start.timetuple())
    context['end'] = time.mktime(end.timetuple())

    with open(folder + '/accelerometer.json', 'w') as outfile:
        json.dump(context, outfile, indent=2)


def visualization(source, generator): # pylint: disable=unused-argument
    filename = settings.MEDIA_ROOT + 'pdk_visualizations/' + source.identifier + '/pdk-sensor-accelerometer/accelerometer.json'

    with open(filename) as infile:
        data = json.load(infile)

        return render_to_string('pdk_sensor_accelerometer_template.html', data)

    return None


def data_table(source, generator): # pylint: disable=unused-argument
    filename = settings.MEDIA_ROOT + 'pdk_visualizations/' + source.identifier + '/pdk-sensor-accelerometer/accelerometer.json'

    with open(filename) as infile:
        data = json.load(infile)

        return render_to_string('pdk_sensor_accelerometer_table_template.html', data)

    return None

def compile_report(generator, sources): # pylint: disable=too-many-locals
    filename = tempfile.gettempdir() + '/pdk_export_' + str(arrow.get().timestamp) + '.zip'

    with ZipFile(filename, 'w', allowZip64=True) as export_file:
        for source in sources:
            identifier = slugify(generator + '__' + source)

            secondary_filename = tempfile.gettempdir() + '/' + identifier + '.txt'

            with open(secondary_filename, 'w') as outfile:
                writer = csv.writer(outfile, delimiter='\t')

                columns = [
                    'Source',
                    'Created Timestamp',
                    'Created Date',
                    'Recorded Timestamp',
                    'Recorded Date',
                    'Raw Timestamp',
                    'Normalized Timestamp',
                    'X',
                    'Y',
                    'Z',
                    'Accuracy'
                ]

                writer.writerow(columns)

                points = DataPoint.objects.filter(source=source, generator_identifier=generator).order_by('created')

                index = 0
                count = points.count()

                while index < count:
                    for point in points[index:(index + 500)]:
                        properties = point.fetch_properties()

                        for i in range(0, len(properties['sensor_data']['observed'])):
                            row = []

                            row.append(point.source)
                            row.append(calendar.timegm(point.created.utctimetuple()))
                            row.append(point.created.isoformat())

                            row.append(calendar.timegm(point.recorded.utctimetuple()))
                            row.append(point.recorded.isoformat())

                            row.append(properties['sensor_data']['raw_timestamp'][i])
                            row.append(properties['sensor_data']['observed'][i])
                            row.append(properties['sensor_data']['x'][i])
                            row.append(properties['sensor_data']['y'][i])
                            row.append(properties['sensor_data']['z'][i])
                            row.append(properties['sensor_data']['accuracy'][i])

                            writer.writerow(row)

                    index += 500

            export_file.write(secondary_filename, slugify(generator) + '/' + slugify(source) + '.txt')

            os.remove(secondary_filename)

    return filename

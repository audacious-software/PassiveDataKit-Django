# pylint: disable=line-too-long, no-member

import calendar
import csv
import datetime
import os
import tempfile

from zipfile import ZipFile

import arrow

from django.template.loader import render_to_string
from django.utils import timezone

from ..models import DataPoint

SECONDARY_IDENTIFIER_ACTIVITY = 'activity-measures'
SECONDARY_IDENTIFIER_INTRADAY = 'intraday-activity'
SECONDARY_IDENTIFIER_SLEEP = 'sleep-measures'
SECONDARY_IDENTIFIER_BODY = 'body'

SECONDARY_FIELDS = {
    'intraday-activity': [
        'intraday_activity_history',
        'activity_start',
        'activity_duration',
        'calories',
        'distance',
        'elevation_climbed',
        'steps',
        'swim_strokes',
        'pool_laps',
    ],
    'body': [
        'measure_date',
        'measure_status',
        'measure_category',
        'measure_type',
        'measure_value',
    ],
    'activity-measures': [
        'date_start',
        'timezone',
        'steps',
        'distance',
        'active_calories',
        'total_calories',
        'elevation',
        'soft_activity_duration',
        'moderate_activity_duration',
        'intense_activity_duration',
    ],
    'sleep-measures': [
        'start_date',
        'end_date',
        'state',
        'measurement_device',
    ]
}

def generator_name(identifier): # pylint: disable=unused-argument
    return 'Withings Device'

def extract_secondary_identifier(properties):
    if 'datastream' in properties:
        return properties['datastream']

    return None


def compile_report(generator, sources): # pylint: disable=too-many-locals
    now = arrow.get()
    filename = tempfile.gettempdir() + '/pdk_export_' + str(now.timestamp) + str(now.microsecond / 1e6) + '.zip'

    with ZipFile(filename, 'w') as export_file:
        for secondary_identifier in SECONDARY_FIELDS:
            secondary_filename = tempfile.gettempdir() + '/' + generator + '-' + \
                                 secondary_identifier + '.txt'

            with open(secondary_filename, 'w') as outfile:
                writer = csv.writer(outfile, delimiter='\t')

                columns = [
                    'Source',
                    'Created Timestamp',
                    'Created Date',
                ]

                for column in SECONDARY_FIELDS[secondary_identifier]:
                    columns.append(column)

                writer.writerow(columns)

                for source in sources:
                    points = DataPoint.objects.filter(source=source, generator_identifier=generator, secondary_identifier=secondary_identifier).order_by('source', 'created') # pylint: disable=no-member,line-too-long

                    index = 0
                    count = points.count()

                    while index < count:
                        for point in points[index:(index + 5000)]:
                            row = []

                            row.append(point.source)
                            row.append(calendar.timegm(point.created.utctimetuple()))
                            row.append(point.created.isoformat())

                            properties = point.fetch_properties()

                            for column in SECONDARY_FIELDS[secondary_identifier]:
                                if column in properties:
                                    row.append(properties[column])
                                else:
                                    row.append('')

                            writer.writerow(row)

                        index += 5000

            export_file.write(secondary_filename, secondary_filename.split('/')[-1])

            os.remove(secondary_filename)

    return filename

def data_table(source, generator):
    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    end = timezone.now()
    start = end - datetime.timedelta(days=7)

    context['activity_values'] = DataPoint.objects.filter(source=source.identifier, generator_identifier=generator, secondary_identifier=SECONDARY_IDENTIFIER_ACTIVITY, created__gt=start, created__lte=end).order_by('created')
    context['intraday_values'] = DataPoint.objects.filter(source=source.identifier, generator_identifier=generator, secondary_identifier=SECONDARY_IDENTIFIER_INTRADAY, created__gt=start, created__lte=end).order_by('created')
    context['sleep_values'] = DataPoint.objects.filter(source=source.identifier, generator_identifier=generator, secondary_identifier=SECONDARY_IDENTIFIER_SLEEP, created__lte=end).order_by('created') # created__gt=start,
    context['body_values'] = DataPoint.objects.filter(source=source.identifier, generator_identifier=generator, secondary_identifier=SECONDARY_IDENTIFIER_BODY, created__lte=end).order_by('created')

    return render_to_string('pdk_wearable_withings_device_table_template.html', context)

import calendar
import csv
import tempfile

from zipfile import ZipFile

import arrow

from ..models import DataPoint

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

def extract_secondary_identifier(properties):
    if 'datastream' in properties:
        return properties['datastream']

    return None


def compile_report(generator, sources): # pylint: disable=too-many-locals
    filename = tempfile.gettempdir() + '/pdk_export_' + str(arrow.get().timestamp) + '.zip'

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

    return filename

# pylint: disable=line-too-long, no-member

import datetime
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
    return 'Device Location'

def visualization(source, generator):
    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    values = []

    end = timezone.now()
    start = end - datetime.timedelta(days=7)

    min_latitude = 90
    max_latitude = -90

    min_longitude = 180
    max_longitude = -180

    for point in DataPoint.objects.filter(source=source.identifier, generator_identifier=generator, created__gt=start, created__lte=end).order_by('created'):
        properties = point.fetch_properties()

        values.append(properties)

        latitude = properties['latitude']
        longitude = properties['longitude']

        if latitude < min_latitude:
            min_latitude = latitude

        if latitude > max_latitude:
            max_latitude = latitude

        if longitude < min_longitude:
            min_longitude = longitude

        if longitude > max_longitude:
            max_longitude = longitude

    context['values'] = values

    context['center_latitude'] = (min_latitude + max_latitude) / 2
    context['center_longitude'] = (min_longitude + max_longitude) / 2

    context['start'] = time.mktime(start.timetuple())
    context['end'] = time.mktime(end.timetuple())

    context['google_api_key'] = settings.PDK_GOOGLE_MAPS_API_KEY

    return render_to_string('pdk_device_location_template.html', context)

def data_table(source, generator):
    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    end = timezone.now()
    start = end - datetime.timedelta(days=1)

    context['values'] = DataPoint.objects.filter(source=source.identifier, generator_identifier=generator, created__gt=start, created__lte=end).order_by('created')

    return render_to_string('pdk_device_location_table_template.html', context)


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

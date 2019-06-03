# pylint: disable=line-too-long, no-member

import calendar
import csv
import datetime
import os
import tempfile
import time

from zipfile import ZipFile

import arrow

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify

from ..models import DataPoint, DataSourceReference, DataGeneratorDefinition

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

    try:
        context['google_api_key'] = settings.PDK_GOOGLE_MAPS_API_KEY
    except AttributeError:
        pass

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

    return render_to_string('pdk_device_location_template.html', context)

def data_table(source, generator):
    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    end = timezone.now()
    start = end - datetime.timedelta(days=1)

    context['values'] = DataPoint.objects.filter(source=source.identifier, generator_identifier=generator, created__gt=start, created__lte=end).order_by('created')

    return render_to_string('pdk_device_location_table_template.html', context)

def compile_report(generator, sources, data_start=None, data_end=None, date_type='created'): # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    now = arrow.get()
    filename = tempfile.gettempdir() + '/pdk_export_' + str(now.timestamp) + str(now.microsecond / 1e6) + '.zip'

    with ZipFile(filename, 'w', allowZip64=True) as export_file:
        for source in sources:
            source_reference = DataSourceReference.reference_for_source(source)
            generator_definition = DataGeneratorDefinition.defintion_for_identifier(generator)

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
                    'Observed',
                    'Raw Timestamp',
                    'Provider',
                    'Latitude',
                    'Longitude',
                    'Accuracy',
                    'Altitude',
                    'Speed',
                    'Bearing',
                ]

                writer.writerow(columns)

                for point in points:
                    properties = point.fetch_properties()

                    row = []

                    row.append(point.source)
                    row.append(calendar.timegm(point.created.utctimetuple()))
                    row.append(point.created.isoformat())

                    row.append(calendar.timegm(point.recorded.utctimetuple()))
                    row.append(point.recorded.isoformat())

                    try:
                        row.append(properties['observed'])
                    except IndexError:
                        row.append('')

                    try:
                        row.append(properties['location_timestamp'])
                    except KeyError:
                        row.append('')

                    try:
                        row.append(properties['provider'])
                    except KeyError:
                        row.append('')

                    try:
                        row.append(properties['latitude'])
                    except KeyError:
                        row.append('')

                    try:
                        row.append(properties['longitude'])
                    except KeyError:
                        row.append('')

                    try:
                        row.append(properties['accuracy'])
                    except KeyError:
                        row.append('')

                    try:
                        row.append(properties['altitude'])
                    except KeyError:
                        row.append('')

                    try:
                        row.append(properties['speed'])
                    except KeyError:
                        row.append('')

                    try:
                        row.append(properties['bearing'])
                    except KeyError:
                        row.append('')

                    writer.writerow(row)

            export_file.write(secondary_filename, slugify(generator) + '/' + slugify(source) + '.txt')

            os.remove(secondary_filename)

    return filename

def extract_location(point):
    properties = point.fetch_properties()

    latitude = properties['latitude']
    longitude = properties['longitude']

    if latitude is not None and longitude is not None:
        point.generated_at = GEOSGeometry('POINT(' + str(longitude) + ' ' + str(latitude) + ')')
        point.save()

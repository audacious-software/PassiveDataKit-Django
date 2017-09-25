# pylint: disable=line-too-long, no-member

import calendar
import csv
import datetime
import json
import os
import tempfile

from zipfile import ZipFile

import arrow
import pytz

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify

from ..models import DataPoint

def generator_name(identifier): # pylint: disable=unused-argument
    return 'Screen State'

def visualization(source, generator):
    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    now = timezone.now()

    days = []

    start = datetime.datetime(now.year, now.month, now.day, 0, 0, 0, 0, pytz.timezone(settings.TIME_ZONE))

    while len(days) < 7:
        end = start + datetime.timedelta(days=1)

        points = DataPoint.objects.filter(source=source.identifier, generator_identifier=generator, created__gt=start, created__lte=end).order_by('created')

        point_list = []

        for point in points:
            properties = point.fetch_properties()

            data_obj = {
                'timestamp': calendar.timegm(point.created.utctimetuple()),
                'value': properties['state']
            }

            point_list.append(data_obj)

        day = {
            'points': point_list,
            'start_txt': start.isoformat(),
            'start': calendar.timegm(start.utctimetuple()),
            'end': calendar.timegm(end.utctimetuple())
        }

        days.insert(0, day)

        start = start - datetime.timedelta(days=1)

    context['days'] = json.dumps(days)

    return render_to_string('pdk_device_screen_state_template.html', context)

def data_table(source, generator):
    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    context['values'] = DataPoint.objects.filter(source=source.identifier, generator_identifier=generator).order_by('-created')[:1000]

    return render_to_string('pdk_screen_state_table_template.html', context)

def compile_report(generator, sources): # pylint: disable=too-many-locals
    filename = tempfile.gettempdir() + '/pdk_export_' + str(arrow.get().timestamp) + '.zip'

    with ZipFile(filename, 'w') as export_file:
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
                    'Screen State'
                ]

                writer.writerow(columns)

                points = DataPoint.objects.filter(source=source, generator_identifier=generator).order_by('created')

                for point in points:
                    properties = point.fetch_properties()

                    row = []

                    row.append(point.source)
                    row.append(calendar.timegm(point.created.utctimetuple()))
                    row.append(point.created.isoformat())

                    row.append(calendar.timegm(point.recorded.utctimetuple()))
                    row.append(point.recorded.isoformat())

                    row.append(properties['state'])

                    writer.writerow(row)

            export_file.write(secondary_filename, slugify(generator) + '/' + slugify(source) + '.txt')

            os.remove(secondary_filename)

    return filename

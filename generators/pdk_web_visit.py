# pylint: disable=line-too-long, no-member

import csv
import calendar
import os
import tempfile

from zipfile import ZipFile

import arrow
import pytz

from django.conf import settings
from django.utils.text import slugify

from ..models import DataPoint

def generator_name(identifier): # pylint: disable=unused-argument
    return 'Web Visit'

def compile_report(generator, sources, data_start=None, data_end=None, date_type='created'): # pylint: disable=too-many-locals
    now = arrow.get()
    filename = tempfile.gettempdir() + '/pdk_export_' + str(now.timestamp) + str(now.microsecond / 1e6) + '.zip'

    with ZipFile(filename, 'w') as export_file:
        for source in sources:
            identifier = slugify(generator + '__' + source)

            secondary_filename = tempfile.gettempdir() + '/' + identifier + '.txt'

            with open(secondary_filename, 'w') as outfile:
                writer = csv.writer(outfile, delimiter='\t')

                columns = [
                    u'Source',
                    u'Created Timestamp',
                    u'Created Date',
                    u'Recorded Timestamp',
                    u'Recorded Date',
                    u'Visit ID',
                    u'URL',
                    u'Protocol',
                    u'Host',
                    u'Title',
                    u'Transition Type',
                    u'Referrer Visit ID',
                ]

                writer.writerow(columns)

                points = DataPoint.objects.filter(source=source, generator_identifier=generator)

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

                for point in points:
                    properties = point.fetch_properties()

                    row = []

                    created = point.created.astimezone(pytz.timezone(settings.TIME_ZONE))
                    recorded = point.recorded.astimezone(pytz.timezone(settings.TIME_ZONE))

                    row.append(point.source)
                    row.append(calendar.timegm(point.created.utctimetuple()))
                    row.append(created.isoformat())
                    row.append(calendar.timegm(point.recorded.utctimetuple()))
                    row.append(recorded.isoformat())

                    row.append(properties['visitId'])
                    row.append(properties['url'].encode('utf-8'))
                    row.append(properties['protocol'])
                    row.append(properties['host'].encode('utf-8'))
                    row.append(properties['title'].encode('utf-8'))
                    row.append(properties['transition'])
                    row.append(properties['referringVisitId'])

                    writer.writerow(row)

            export_file.write(secondary_filename, slugify(generator) + '/' + slugify(source) + '.txt')

            os.remove(secondary_filename)

    return filename

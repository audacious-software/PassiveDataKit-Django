# pylint: disable=line-too-long, no-member

import datetime

from django.template.loader import render_to_string
from django.utils import timezone

from ..models import DataPoint

def extract_secondary_identifier(properties):
    if 'application' in properties:
        return properties['application']

    return None

def generator_name(identifier): # pylint: disable=unused-argument
    return 'Foreground Application'

# def visualization(source, generator):
#    context = {}
#    context['source'] = source
#    context['generator_identifier'] = generator
#
#    values = []
#
#    end = timezone.now()
#    start = end - datetime.timedelta(days=1)
#
#    last_value = -1
#
#    for point in DataPoint.objects.filter(source=source.identifier, generator_identifier=generator, created__gt=start, created__lte=end).order_by('created'):
#        properties = point.fetch_properties()
#
#        if last_value != properties['level']:
#            value = {}
#
#            value['ts'] = properties['passive-data-metadata']['timestamp']
#            value['value'] = properties['level']
#
#            last_value = properties['level']
#
#            values.append(value)
#
#    context['values'] = values
#
#    context['start'] = time.mktime(start.timetuple())
#    context['end'] = time.mktime(end.timetuple())
#
#    return render_to_string('pdk_device_battery_template.html', context)

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

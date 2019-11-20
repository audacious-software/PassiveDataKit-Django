# pylint: disable=line-too-long, no-member

import bz2
import calendar
import csv
import gc
import importlib
import json
import os
import tempfile
import traceback

import StringIO

import dropbox
import paramiko

from django.conf import settings
from django.core import management
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify

from .models import DataPoint, DataBundle, DataGeneratorDefinition, DataSourceReference, install_supports_jsonfield

# def name_for_generator(identifier):
#    if identifier == 'web-historian':
#        return 'Web Historian Web Visits'
#
#    return None

# def compile_visualization(identifier, points_query, folder):
#
#    if identifier == 'web-historian':
#

def visualization(source, generator):
    try:
        generator_module = importlib.import_module('.generators.' + generator.replace('-', '_'), package='passive_data_kit')

        output = generator_module.visualization(source, generator)

        if output is not None:
            return output
    except ImportError:
        # traceback.print_exc()
        pass
    except AttributeError:
        # traceback.print_exc()
        pass

    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    rows = []

    for point in DataPoint.objects.filter(source=source.identifier, generator_identifier=generator).order_by('-created')[:1000]:
        row = {}

        row['created'] = point.created
        row['value'] = '-'

        rows.append(row)

    context['table_rows'] = rows

    return render_to_string('pdk_generic_viz_template.html', context)

def data_table(source, generator):
    for app in settings.INSTALLED_APPS:
        try:
            generator_module = importlib.import_module('.generators.' + generator.replace('-', '_'), package=app)

            output = generator_module.data_table(source, generator)

            if output is not None:
                return output
        except ImportError:
            pass
        except AttributeError:
            pass

    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    rows = []

    for point in DataPoint.objects.filter(source=source.identifier, generator_identifier=generator).order_by('-created')[:1000]:
        row = {}

        row['created'] = point.created
        row['value'] = '-'

        rows.append(row)

    context['table_rows'] = rows

    return render_to_string('pdk_generic_viz_template.html', context)

def compile_report(generator, sources, data_start=None, data_end=None, date_type='created'): # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    try:
        generator_module = importlib.import_module('.generators.' + generator.replace('-', '_'), package='passive_data_kit')

        output_file = None

        try:
            output_file = generator_module.compile_report(generator, sources, data_start=data_start, data_end=data_end, date_type=date_type)
        except TypeError:
            print 'TODO: Update ' + generator + '.compile_report to support data_start, data_end, and date_type parameters!'

            output_file = generator_module.compile_report(generator, sources)

        if output_file is not None:
            return output_file
    except ImportError:
        pass
    except AttributeError:
        pass

    filename = tempfile.gettempdir() + '/' + generator + '.txt'

    with open(filename, 'w') as outfile:
        writer = csv.writer(outfile, delimiter='\t')

        writer.writerow([
            'Source',
            'Generator',
            'Generator Identifier',
            'Created Timestamp',
            'Created Date',
            'Latitude',
            'Longitude',
            'Recorded Timestamp',
            'Recorded Date',
            'Properties'
        ])

        generator_definition = DataGeneratorDefinition.definition_for_identifier(generator)

        for source in sources:
            source_reference = DataSourceReference.reference_for_source(source)

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

            index = 0
            count = points.count()

            while index < count:
                for point in points[index:(index + 5000)]:
                    row = []

                    row.append(point.source)
                    row.append(point.generator)
                    row.append(point.generator_identifier)
                    row.append(calendar.timegm(point.created.utctimetuple()))
                    row.append(point.created.isoformat())

                    if point.generated_at is not None:
                        row.append(point.generated_at.y)
                        row.append(point.generated_at.x)
                    else:
                        row.append('')
                        row.append('')

                    row.append(calendar.timegm(point.recorded.utctimetuple()))
                    row.append(point.recorded.isoformat())
                    row.append(json.dumps(point.fetch_properties()))

                    writer.writerow(row)

                index += 5000

    return filename

def compile_visualization(identifier, points, folder):
    try:
        generator_module = importlib.import_module('.generators.' + identifier.replace('-', '_'), package='passive_data_kit')

        generator_module.compile_visualization(identifier, points, folder)
    except ImportError:
        pass
    except AttributeError:
        pass

def extract_location_method(identifier):
    try:
        generator_module = importlib.import_module('.generators.' + identifier.replace('-', '_'), package='passive_data_kit')

        return generator_module.extract_location
    except ImportError:
        pass
    except AttributeError:
        pass

    return None

def send_to_destination(destination, report_path):
    file_sent = False

    if destination.destination == 'dropbox':
        try:
            parameters = destination.fetch_parameters()

            if 'access_token' in parameters:
                client = dropbox.Dropbox(parameters['access_token'])

                path = '/'

                if 'path' in parameters:
                    path = parameters['path']

                path = path + '/'

                if ('prepend_date' in parameters) and parameters['prepend_date']:
                    path = path + timezone.now().date().isoformat() + '-'

                path = path + os.path.basename(os.path.normpath(report_path))

                with open(report_path, 'rb') as report_file:
                    client.files_upload(report_file.read(), path)

                file_sent = True
        except BaseException:
            traceback.print_exc()
    elif destination.destination == 'sftp':
        try:
            parameters = destination.fetch_parameters()

            if ('username' in parameters) and ('host' in parameters) and ('key' in parameters):
                path = ''

                if 'path' in parameters:
                    path = parameters['path']

                if ('prepend_date' in parameters) and parameters['prepend_date']:
                    path = path + timezone.now().date().isoformat() + '-'

                path = path + os.path.basename(os.path.normpath(report_path))

                key = paramiko.RSAKey.from_private_key(StringIO.StringIO(parameters['key']))

                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(hostname=parameters['host'], username=parameters['username'], pkey=key)

                ftp_client = ssh_client.open_sftp()
                ftp_client.put(report_path, path)
                ftp_client.close()

                file_sent = True
        except BaseException:
            traceback.print_exc()

    if file_sent is False:
        print 'Unable to transmit report to destination "' + destination.destination + '".'

def annotate_source_definition(source, definition):
    active_alerts = []

    for alert in source.alerts.filter(active=True):
        active_alerts.append(alert.fetch_definition())

    definition['active_alerts'] = active_alerts

    earliest_point = source.earliest_point()

    if earliest_point is not None:
        definition['earliest_point'] = {
            'pk': earliest_point.pk,
            'generator_identifier': earliest_point.generator_identifier,
            'created': earliest_point.created.isoformat(),
            'recorded': earliest_point.recorded.isoformat()
        }
    else:
        definition['earliest_point'] = None

    latest_point = source.latest_point()

    if latest_point is not None:
        definition['latest_point'] = {
            'pk': latest_point.pk,
            'generator_identifier': latest_point.generator_identifier,
            'created': latest_point.created.isoformat(),
            'recorded': latest_point.recorded.isoformat()
        }
    else:
        definition['latest_point'] = None

    return definition

def load_backup(filename, content):
    prefix = 'pdk_backup_' + settings.ALLOWED_HOSTS[0]

    if filename.startswith(prefix) is False:
        return

    if 'json-dumpdata' in filename:
        filename = filename.replace('.json-dumpdata.bz2.encrypted', '.json')

        path = os.path.join(tempfile.gettempdir(), filename)

        with open(path, 'wb') as fixture_file:
            fixture_file.write(content)

        management.call_command('loaddata', path)

        os.remove(path)
    elif 'pdk-bundle' in filename:
        bundle = DataBundle(recorded=timezone.now())

        if install_supports_jsonfield():
            bundle.properties = json.loads(content)
        else:
            bundle.properties = content

        bundle.save()
    else:
        print '[passive_data_kit.pdk_api.load_backup] Unknown file type: ' + filename

def incremental_backup(parameters): # pylint: disable=too-many-locals, too-many-statements
    to_transmit = []
    to_clear = []

    # Dump full content of these models. No incremental backup here.

    dumpdata_apps = (
        'auth',
        'passive_data_kit.AppConfiguration',
        'passive_data_kit.DataServerApiToken',
        'passive_data_kit.DataServerAccessRequest',
        'passive_data_kit.DataServer',
        'passive_data_kit.DataSourceGroup',
        'passive_data_kit.DataSource',
        'passive_data_kit.DeviceIssue',
        'passive_data_kit.DeviceModel',
        'passive_data_kit.Device',
        'passive_data_kit.ReportDestination',
    )

    prefix = 'pdk_backup_' + settings.ALLOWED_HOSTS[0]

    if 'start_date' in parameters:
        prefix += '_' + parameters['start_date'].isoformat()

    if 'end_date' in parameters:
        prefix += '_' + parameters['end_date'].isoformat()

    backup_staging = tempfile.gettempdir()

    try:
        backup_staging = settings.PDK_BACKUP_STAGING_DESTINATION
    except AttributeError:
        pass

    for app in dumpdata_apps:
        print '[passive_data_kit] Backing up ' + app + '...'
        buf = StringIO.StringIO()
        management.call_command('dumpdata', app, stdout=buf)
        buf.seek(0)

        database_dump = buf.read()

        buf = None

        gc.collect()

        compressed_str = bz2.compress(database_dump)

        database_dump = None

        gc.collect()

        filename = prefix + '_' + slugify(app) + '.json-dumpdata.bz2'

        path = os.path.join(backup_staging, filename)

        with open(path, 'wb') as fixture_file:
            fixture_file.write(compressed_str)

        to_transmit.append(path)

    # Using parameters, only backup matching DataPoint objects. Add PKs to to_clear for
    # optional deletion.

    bundle_size = 500

    try:
        bundle_size = settings.PDK_BACKUP_BUNDLE_SIZE
    except AttributeError:
        print 'Define PDK_BACKUP_BUNDLE_SIZE in the settings to define the size of backup payloads.'

    query = Q(generator_identifier__startswith='pdk-')

    if 'start_date' in parameters:
        query = query & Q(recorded__gte=parameters['start_date'])

    if 'end_date' in parameters:
        query = query & Q(recorded__lt=parameters['end_date'])

    clear_archived = False

    if 'clear_archived' in parameters and parameters['clear_archived']:
        clear_archived = True

    count = DataPoint.objects.filter(query).count()

    index = 0

    while index < count:
        filename = prefix + '_data_points_' + str(index) + '_' + str(count) + '.pdk-bundle.bz2'

        print '[passive_data_kit] Backing up data points ' + str(index) + ' of ' + str(count) + '...'

        bundle = []

        for point in DataPoint.objects.filter(query).order_by('recorded')[index:(index + bundle_size)]:
            bundle.append(point.fetch_properties())

            if clear_archived:
                to_clear.append('pdk:' + str(point.pk))

        index += bundle_size

        compressed_str = bz2.compress(json.dumps(bundle))

        path = os.path.join(backup_staging, filename)

        with open(path, 'wb') as compressed_file:
            compressed_file.write(compressed_str)

        to_transmit.append(path)

    return to_transmit, to_clear


def clear_points(to_clear):
    for point_id in to_clear:
        point_pk = int(point_id.replace('pdk:', ''))

        DataPoint.objects.filter(pk=point_pk).delete()

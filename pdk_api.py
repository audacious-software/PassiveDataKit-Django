# pylint: disable=line-too-long, no-member

from __future__ import print_function

from builtins import str # pylint: disable=redefined-builtin
from builtins import range # pylint: disable=redefined-builtin

import bz2
import calendar
import csv
import datetime
import gc
import importlib
import json
import os
import re
import sys
import shutil
import tempfile
import time
import traceback

from io import StringIO

import dropbox
import paramiko

from django.conf import settings
from django.core import management
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify

from .models import DataPoint, DataBundle, DataGeneratorDefinition, DataSourceReference, install_supports_jsonfield

def filter_structure(pattern, structure, prefix=''):
    if isinstance(structure, dict):
        to_filter = []

        for key in structure:
            key_path = prefix + '.' + str(key)

            while key_path.startswith('.'):
                key_path = key_path[1:]

            filter_structure(pattern, structure[key], prefix=key_path)

            if pattern.match(key_path):
                to_filter.append(key)

        for key in to_filter:
            del structure[key]

    elif isinstance(structure, list):
        to_filter = []

        for key_index in range(0, len(structure)): # pylint: disable=consider-using-enumerate
            key_path = prefix + '.' + str(key_index)

            while key_path.startswith('.'):
                key_path = key_path[1:]

            filter_structure(pattern, structure[key_index], prefix=key_path)

            if pattern.match(key_path):
                to_filter.append(key_index)

        for key_index in to_filter.reverse():
            del structure[key_index]
    else:
        pass # Nothing to do for other variable types


def filter_sensitive_fields(point, point_properties, parameters):
    if hasattr(settings, 'PDK_SENSITIVE_FIELDS') and 'filter_sensitive' in parameters and parameters['filter_sensitive'] is not False:
        if point.generator_identifier in settings.PDK_SENSITIVE_FIELDS:
            sensitive_fields = settings.PDK_SENSITIVE_FIELDS[point.generator_identifier]

            for sensitive_field in sensitive_fields:
                filter_structure(re.compile(sensitive_field), point_properties)

    return point_properties



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
            print('TODO: Update ' + generator + '.compile_report to support data_start, data_end, and date_type parameters!')

            output_file = generator_module.compile_report(generator, sources)

        if output_file is not None:
            return output_file
    except ImportError:
        pass
    except AttributeError:
        pass

    filename = tempfile.gettempdir() + os.path.sep + generator + '.txt'

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

                    writer.writerow([s.encode('utf-8') for s in row])

                index += 5000

    return filename

def compile_visualization(identifier, points, folder, source=None):
    try:
        generator_module = importlib.import_module('.generators.' + identifier.replace('-', '_'), package='passive_data_kit')

        try:
            generator_module.compile_visualization(identifier, points, folder, source)
        except TypeError:
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

def send_to_destination(destination, report_path): # pylint: disable=too-many-branches, too-many-statements
    file_sent = False

    sleep_durations = [
        0,
        60,
        120,
        300,
    ]

    try:
        sleep_durations = settings.PDK_UPLOAD_SLEEP_DURATIONS
    except AttributeError:
        pass # Use defaults above.

    if destination.destination == 'dropbox':
        try:
            parameters = destination.fetch_parameters()

            if 'access_token' in parameters:
                client = dropbox.Dropbox(parameters['access_token'])

                path = '/'

                if 'path' in parameters:
                    path = parameters['path']

                path = path + '/'

                if ('prepend_host' in parameters) and parameters['prepend_host']:
                    path = path + settings.ALLOWED_HOSTS[0] + '-'

                if ('prepend_date' in parameters) and parameters['prepend_date']:
                    path = path + timezone.now().date().isoformat() + '-'

                path = path + os.path.basename(os.path.normpath(report_path))

                for duration in sleep_durations:
                    time.sleep(duration)

                    try:
                        with open(report_path, 'rb') as report_file:
                            client.files_upload(report_file.read(), path)

                            file_sent = True
                    except: # pylint: disable=bare-except
                        if duration == sleep_durations[-1]:
                            print('Unable to upload - error encountered. (Latest sleep = ' + str(duration) + ' seconds.)')

                            traceback.print_exc()

        except BaseException:
            traceback.print_exc()
    elif destination.destination == 'sftp': # pylint: disable=too-many-nested-blocks
        try:
            parameters = destination.fetch_parameters()

            if ('username' in parameters) and ('host' in parameters) and ('key' in parameters):
                path = ''

                if 'path' in parameters:
                    path = parameters['path']

                if ('prepend_date' in parameters) and parameters['prepend_date']:
                    path = path + timezone.now().date().isoformat() + '-'

                path = path + os.path.basename(os.path.normpath(report_path))

                for duration in sleep_durations:
                    time.sleep(duration)

                    try:
                        key = paramiko.RSAKey.from_private_key(StringIO(parameters['key']))

                        ssh_client = paramiko.SSHClient()

                        trust_host_keys = True

                        try:
                            trust_host_keys = settings.PDK_API_TRUST_HOST_KEYS
                        except AttributeError:
                            pass

                        if trust_host_keys:
                            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # lgtm[py/paramiko-missing-host-key-validation]

                        ssh_client.connect(hostname=parameters['host'], username=parameters['username'], pkey=key)

                        ftp_client = ssh_client.open_sftp()
                        ftp_client.put(report_path, path)
                        ftp_client.close()

                        file_sent = True
                    except: # pylint: disable=bare-except
                        if duration == sleep_durations[-1]:
                            print('Unable to upload - error encountered. (Latest sleep = ' + str(duration) + ' seconds.)')

                            traceback.print_exc()

        except BaseException:
            traceback.print_exc()

    elif destination.destination == 'local':
        try:
            parameters = destination.fetch_parameters()

            if 'path' in parameters:
                path = parameters['path']

            if ('prepend_date' in parameters) and parameters['prepend_date']:
                path = path + timezone.now().date().isoformat() + '-'

            path = path + os.path.basename(os.path.normpath(report_path))

            shutil.copyfile(report_path, path)

            file_sent = True

        except BaseException:
            traceback.print_exc()

    if file_sent is False:
        print('Unable to transmit report to destination "' + destination.destination + '".')

def annotate_source_definition(source, definition):
    active_alerts = []

    for alert in source.alerts.filter(active=True):
        active_alerts.append(alert.fetch_definition())

    definition['active_alerts'] = active_alerts

    earliest_point = None # source.earliest_point()

    if earliest_point is not None:
        definition['earliest_point'] = {
            'pk': earliest_point.pk,
            'generator_identifier': earliest_point.generator_identifier,
            'created': earliest_point.created.isoformat(),
            'recorded': earliest_point.recorded.isoformat()
        }
    else:
        definition['earliest_point'] = None

    latest_point = None # source.latest_point()

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
        backup_content = json.loads(content)

        bundle_index = 0

        while backup_content:
            bundle_content = []

            if (bundle_index % 50) == 0:
                print('[passive_data_kit.pdk_api.load_backup] ' + str(len(backup_content)) + ' items remaining to write...')

            while backup_content and len(bundle_content) < 100:
                bundle_content.append(backup_content.pop(0))

            if bundle_content:
                bundle = DataBundle(recorded=timezone.now())

                if install_supports_jsonfield():
                    bundle.properties = bundle_content
                else:
                    bundle.properties = json.dumps(bundle_content, indent=2)

                bundle.save()

                bundle_index += 1
    else:
        print('[passive_data_kit.pdk_api.load_backup] Unknown file type: ' + filename)

def incremental_backup(parameters): # pylint: disable=too-many-locals, too-many-statements, too-many-branches
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

    if parameters['skip_apps']:
        dumpdata_apps = ()

    prefix = 'pdk_backup_' + settings.ALLOWED_HOSTS[0]

    if 'start_date' in parameters:
        prefix += '_' + parameters['start_date'].date().isoformat()

    if 'end_date' in parameters:
        prefix += '_' + (parameters['end_date'].date() - datetime.timedelta(days=1)).isoformat()

    backup_staging = tempfile.gettempdir()

    try:
        backup_staging = settings.PDK_BACKUP_STAGING_DESTINATION
    except AttributeError:
        pass

    for app in dumpdata_apps:
        print('[passive_data_kit] Backing up ' + app + '...')
        sys.stdout.flush()

        buf = StringIO()
        management.call_command('dumpdata', app, stdout=buf)
        buf.seek(0)

        database_dump = buf.read()

        buf = None

        gc.collect()

        compressed_str = bz2.compress(database_dump.encode('utf-8'))

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
        print('Define PDK_BACKUP_BUNDLE_SIZE in the settings to define the size of backup payloads.')

    query = None

    for definition in DataGeneratorDefinition.objects.all():
        if definition.generator_identifier.startswith('pdk-'):
            if query is None:
                query = Q(generator_definition=definition)
            else:
                query = query | Q(generator_definition=definition)

    if 'start_date' in parameters:
        if query is not None:
            query = query & Q(recorded__gte=parameters['start_date'])
        else:
            query = Q(recorded__gte=parameters['start_date'])

    if 'end_date' in parameters:
        if query is not None:
            query = query & Q(recorded__lt=parameters['end_date'])
        else:
            query = Q(recorded__lt=parameters['end_date'])

    clear_archived = False

    if 'clear_archived' in parameters and parameters['clear_archived']:
        clear_archived = True

    print('[passive_data_kit] Fetching count of data points...')
    sys.stdout.flush()

    count = DataPoint.objects.filter(query).count()

    index = 0

    while index < count:
        filename = prefix + '_data_points_' + str(index) + '_' + str(count) + '.pdk-bundle.bz2'

        print('[passive_data_kit] Backing up data points ' + str(index) + ' of ' + str(count) + '...')
        sys.stdout.flush()

        bundle = []

        for point in DataPoint.objects.filter(query).order_by('recorded')[index:(index + bundle_size)]:
            bundle.append(filter_sensitive_fields(point, point.fetch_properties(), parameters))

            if clear_archived:
                to_clear.append('pdk:' + str(point.pk))

        index += bundle_size

        compressed_str = bz2.compress(json.dumps(bundle).encode('utf-8'))

        path = os.path.join(backup_staging, filename)

        with open(path, 'wb') as compressed_file:
            compressed_file.write(compressed_str)

        to_transmit.append(path)

    return to_transmit, to_clear

def clear_points(to_clear):
    point_count = len(to_clear)

    for i in range(0, point_count):
        if (i % 1000) == 0:
            print('[passive_data_kit] Clearing points ' + str(i) + ' of ' + str(point_count) + '...')
            sys.stdout.flush()

        point_id = to_clear[i]

        point_pk = int(point_id.replace('pdk:', ''))

        DataPoint.objects.filter(pk=point_pk).delete()

def update_data_type_definition(definition):
    if 'passive-data-metadata.timestamp' in definition:
        del definition['passive-data-metadata.timestamp']['range']

        definition['passive-data-metadata.timestamp']['types'] = ['integer', 'real']

        definition['passive-data-metadata.timestamp']['pdk_variable_name'] = 'Creation time'
        definition['passive-data-metadata.timestamp']['pdk_variable_description'] = 'Unix timestamp (in seconds) encoding the moment in time the data point was generated. Note that this is NOT the same as the time when it was recorded on the server.'

    if 'passive-data-metadata.source' in definition:
        del definition['passive-data-metadata.source']['observed']

        definition['passive-data-metadata.source']['is_freetext'] = True

        definition['passive-data-metadata.source']['pdk_variable_name'] = 'Source identifier'
        definition['passive-data-metadata.source']['pdk_variable_description'] = 'Unique identifier of the source of the data point. Often identifies specific people or devices engaged in passive data generation.'

    if 'passive-data-metadata.generator-id' in definition:
        definition['passive-data-metadata.generator-id']['is_freetext'] = True

        definition['passive-data-metadata.generator-id']['pdk_variable_name'] = 'Generator identifier'
        definition['passive-data-metadata.generator-id']['pdk_variable_description'] = 'Unique identifier of the data point type.'

    if 'passive-data-metadata.generator' in definition:
        del definition['passive-data-metadata.generator']['observed']

        definition['passive-data-metadata.generator']['is_freetext'] = True

        definition['passive-data-metadata.generator']['pdk_variable_name'] = 'Generator identifier (descriptive)'
        definition['passive-data-metadata.generator']['pdk_variable_description'] = 'Identifies the data point type as well as the name and version of the software that generated the data point.'

    if 'passive-data-metadata' in definition:
        definition['passive-data-metadata']['pdk_variable_name'] = 'Standard Passive Data Kit metadata container'
        definition['passive-data-metadata']['pdk_variable_description'] = 'Collection of values common across all data points, identifing the source, type, and software that produced a data point.'

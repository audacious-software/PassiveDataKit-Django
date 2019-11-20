# pylint: disable=no-member,line-too-long

import base64
import datetime
import importlib
import os
import sys
import urlparse

import StringIO

import dropbox
import pytz

from nacl.secret import SecretBox

from django.conf import settings
from django.core.management.base import BaseCommand

from passive_data_kit.decorators import handle_lock

class Command(BaseCommand):
    help = 'Generates incremental backups of data content and transmits to storage.'

    def add_arguments(self, parser):
        parser.add_argument('--start-date',
                            type=str,
                            dest='start_date',
                            default=None,
                            help='Start of date range for incremental backup')

        parser.add_argument('--end-date',
                            type=str,
                            dest='end_date',
                            default=None,
                            help='End of date range for incremental backup')

        parser.add_argument('--clear-archived',
                            dest='clear_archived',
                            action='store_true',
                            help='Delete backed-up content after successful transmission')


    def folder_for_options(self, options): # pylint: disable=no-self-use
        folder_path_format = '%(start_date)s__%(end_date)s'

        try:
            folder_path_format = settings.PDK_BACKUP_FOLDER_FORMAT
        except AttributeError:
            pass

        folder_args = {}

        if 'start_date' in options:
            folder_args['start_date'] = str(options['start_date'])

        if 'end_date' in options:
            folder_args['end_date'] = str(options['end_date'])

        if 'clear_archived' in options and options['clear_archived']:
            folder_args['clear'] = 'data-cleared'
        else:
            folder_args['clear'] = 'data-retained'

        return folder_path_format % folder_args


    @handle_lock
    def handle(self, *args, **options): # pylint: disable=too-many-locals, too-many-statements, too-many-branches
        here_tz = pytz.timezone(settings.TIME_ZONE)

        parameters = {}

        if options['start_date'] is not None:
            components = options['start_date'].split('-')

            start_date = datetime.datetime(int(components[0]), int(components[1]), int(components[2]), 0, 0, 0, 0, here_tz)

            parameters['start_date'] = start_date

        if options['end_date'] is not None:
            components = options['end_date'].split('-')

            end_date = datetime.datetime(int(components[0]), int(components[1]), int(components[2]), 0, 0, 0, 0, here_tz) + datetime.timedelta(days=1)

            parameters['end_date'] = end_date

        parameters['clear_archived'] = options['clear_archived']

        key = None

        try:
            key = base64.b64decode(settings.PDK_BACKUP_KEY)
        except AttributeError:
            print 'Please define PDK_BACKUP_KEY in the settings.'

            sys.exit(1)

        destinations = None

        try:
            destinations = settings.PDK_BACKUP_DESTINATIONS
        except AttributeError:
            print 'Please define PDK_BACKUP_DESTINATIONS in the settings.'

            sys.exit(1)

        for app in settings.INSTALLED_APPS:
            try:
                pdk_api = importlib.import_module(app + '.pdk_api')

                to_transmit, to_clear = pdk_api.incremental_backup(parameters)

                for destination in destinations:
                    destination_url = urlparse.urlparse(destination)

                    if destination_url.scheme == 'file':
                        dest_path = destination_url.path

                        final_folder = self.folder_for_options(options)

                        if final_folder is not None:
                            dest_path = os.path.join(dest_path, final_folder)

                        if os.path.exists(dest_path) is False:
                            print 'Creating folder for archive storage: ' + dest_path
                            os.makedirs(dest_path)

                        for path in to_transmit:
                            box = SecretBox(key)

                            with open(path, 'rb') as backup_file:
                                encrypted_str = box.encrypt(backup_file.read())

                                filename = os.path.basename(path) + '.encrypted'

                                encrypted_path = os.path.join(dest_path, filename)

                                print 'Writing to filesystem: ' + encrypted_path

                                with open(encrypted_path, 'wb') as encrypted_file:
                                    encrypted_file.write(encrypted_str)

                            os.remove(path)
                    elif destination_url.scheme == 'dropbox':
                        access_token = destination_url.netloc

                        client = dropbox.Dropbox(access_token)

                        for path in to_transmit:
                            box = SecretBox(key)

                            with open(path, 'rb') as backup_file:
                                encrypted_io = StringIO.StringIO()
                                encrypted_io.write(backup_file.read())
                                encrypted_io.seek(0)

                                filename = os.path.basename(path) + '.encrypted'

                                dropbox_path = os.path.join(destination_url.path, filename)

                                print 'Uploading to Dropbox: ' + encrypted_path

                                client.files_upload(encrypted_io.read(), dropbox_path)

                            os.remove(path)
                    else:
                        print 'Unknown desitination: ' + destination

                pdk_api.clear_points(to_clear)

            except ImportError:
                pass
            except AttributeError:
                pass

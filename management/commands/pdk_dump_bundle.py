# pylint: disable=no-member,line-too-long

from __future__ import print_function

from builtins import str # # pylint: disable=redefined-builtin

import base64
import gzip
import json

import io

import six

from nacl.public import PublicKey, PrivateKey, Box

from django.conf import settings
from django.core.management.base import BaseCommand

from ...decorators import handle_lock
from ...models import DataBundle, install_supports_jsonfield

class Command(BaseCommand):
    help = 'Prints the content of a bundle to the terminal, uncompressing and decrypting if necessary.'

    def add_arguments(self, parser):
        parser.add_argument('bundle_pk',
                            nargs=1,
                            type=int,
                            help='PK of bundle to dump')

    @handle_lock
    def handle(self, *args, **options): # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        supports_json = install_supports_jsonfield()

        bundle = DataBundle.objects.get(pk=options['bundle_pk'][0])

        if supports_json is False:
            bundle.properties = json.loads(bundle.properties)

        if bundle.encrypted:
            if 'nonce' in bundle.properties and 'encrypted' in bundle.properties:
                payload = base64.b64decode(bundle.properties['encrypted'])
                nonce = base64.b64decode(bundle.properties['nonce'])

                private_key = PrivateKey(base64.b64decode(settings.PDK_SERVER_KEY).strip()) # pylint: disable=line-too-long
                public_key = PublicKey(base64.b64decode(settings.PDK_CLIENT_KEY).strip()) # pylint: disable=line-too-long

                box = Box(private_key, public_key)

                decrypted_message = box.decrypt(payload, nonce)

                decrypted = six.text_type(decrypted_message, encoding='utf8')

                if bundle.compression != 'none':
                    compressed = base64.b64decode(decrypted)

                    if bundle.compression == 'gzip':
                        fio = io.StringIO(compressed)  # io.BytesIO for Python 3
                        gzip_file_obj = gzip.GzipFile(fileobj=fio)
                        payload = gzip_file_obj.read()
                        gzip_file_obj.close()

                        decrypted = payload

                bundle.properties = json.loads(decrypted)
            elif 'encrypted' in bundle.properties:
                print('Missing "nonce" in encrypted bundle. Cannot decrypt bundle ' + str(bundle.pk) + '. Skipping...')
            elif 'nonce' in bundle.properties:
                print('Missing "encrypted" in encrypted bundle. Cannot decrypt bundle ' + str(bundle.pk) + '. Skipping...')
        elif bundle.compression != 'none':
            compressed = base64.b64decode(bundle.properties['payload'])

            if bundle.compression == 'gzip':
                fio = io.StringIO(compressed)  # io.BytesIO for Python 3
                gzip_file_obj = gzip.GzipFile(fileobj=fio)
                payload = gzip_file_obj.read()
                gzip_file_obj.close()

                bundle.properties = json.loads(payload)

        print(json.dumps(bundle.properties, indent=2))

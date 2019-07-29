# pylint: disable=no-member,line-too-long

import base64
import json

import six

from nacl.public import PublicKey, PrivateKey, Box

from django.conf import settings
from django.core.management.base import BaseCommand

from ...decorators import handle_lock
from ...models import DataPoint, DataBundle, install_supports_jsonfield, DataSourceReference, DataSource, DataSourceAlert

class Command(BaseCommand):
    help = 'Remove data associated with a specific source identifier.'

    def add_arguments(self, parser):
        parser.add_argument('--source',
                            type=str,
                            dest='source',
                            default=None,
                            help='Identifier of the source to remove')

    @handle_lock
    def handle(self, *args, **options): # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        source = options['source']

        supports_json = install_supports_jsonfield()

        # Remove bundles

        deleted = 0
        partial_bundles = 0

        to_delete = []

        for bundle in DataBundle.objects.all():
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

                    bundle.properties = json.loads(decrypted)
                elif 'encrypted' in bundle.properties:
                    print 'Missing "nonce" in encrypted bundle. Cannot decrypt bundle ' + str(bundle.pk) + '. Skipping...'
                    break
                elif 'nonce' in bundle.properties:
                    print 'Missing "encrypted" in encrypted bundle. Cannot decrypt bundle ' + str(bundle.pk) + '. Skipping...'
                    break

            total_points = len(bundle.properties)

            for data_point in bundle.properties:
                if source == data_point['passive-data-metadata']['source']:
                    total_points -= 1

            if total_points == 0:
                to_delete.append(bundle)
            elif total_points != len(bundle.properties):
                partial_bundles += 1

        for bundle in to_delete:
            bundle.delete()

        print 'Removed ' + str(len(to_delete)) + ' DataBundle objects.'
        print 'Found ' + str(partial_bundles) + ' partial DataBundle objects (not removed).'

        source_reference = DataSourceReference.reference_for_source(source)

        if source_reference is not None:
            deleted = DataPoint.objects.filter(source_reference=source_reference)

            print 'Removed ' + str(deleted) + ' DataPoint objects by source reference.'

        source_reference.delete()

        print 'Removed DataSourceReference object.'

        deleted = DataPoint.objects.filter(source=source)

        print 'Removed ' + str(deleted) + ' DataPoint objects by source match.'

        source_obj = DataSource.objects.filter(identifier=source).first()

        if source_obj is not None:
            deleted = DataSourceAlert.objects.filter(data_source=source_obj).delete()

            print 'Removed ' + str(deleted) + ' DataSourceAlert objects by source match.'

            source_obj.delete()

            print 'Removed DataSource object.'

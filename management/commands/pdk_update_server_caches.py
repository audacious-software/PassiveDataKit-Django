# pylint: disable=no-member

import json

from django.core.management.base import BaseCommand
from django.db.models import Q

from ...decorators import handle_lock
from ...models import DataPoint, DataServerMetadatum, GENERATORS_DATUM, SOURCES_DATUM

class Command(BaseCommand):
    help = 'Updates server caches to speed up operations'

    @handle_lock
    def handle(self, *args, **options):
        identifiers = DataServerMetadatum.objects.filter(key=GENERATORS_DATUM).first()

        seen_identifiers = []
        conditions = Q(generator_identifier__exact=None)

        if identifiers is None:
            identifiers = DataServerMetadatum(key=GENERATORS_DATUM)
        else:
            seen_identifiers = json.loads(identifiers.value)

            for identifier in seen_identifiers:
                conditions = conditions | Q(generator_identifier=identifier)

#        print('CONDITIONS[0]: ' + str(conditions))

        data_point = DataPoint.objects.exclude(conditions).first()

        while data_point is not None:
#            print('APPENDING[L] ' + data_point.generator_identifier)

            seen_identifiers.append(data_point.generator_identifier)

            conditions = conditions | Q(generator_identifier=data_point.generator_identifier)

#            print('CONDITIONS[L]: ' + str(conditions))

            data_point = DataPoint.objects.exclude(conditions).first()

#            print('DP: ' + str(data_point))

        seen_identifiers.sort()

#        print('GATHERED IDS: ' + json.dumps(seen_identifiers, indent=2))

        identifiers.value = json.dumps(seen_identifiers, indent=2)

        identifiers.save()

        sources = DataServerMetadatum.objects.filter(key=SOURCES_DATUM).first()

        seen_sources = []
        conditions = Q(source__exact=None)

        if sources is None:
            sources = DataServerMetadatum(key=SOURCES_DATUM)
        else:
            seen_sources = json.loads(sources.value)

            for source in seen_sources:
                conditions = conditions | Q(source=source)

#        print('CONDITIONS[0S]: ' + str(conditions))

        data_point = DataPoint.objects.exclude(conditions).first()

        while data_point is not None:
#            print('APPENDING[LS] ' + data_point.source)

            seen_sources.append(data_point.source)

            conditions = conditions | Q(generator_identifier__exact=data_point.source)

#            print('CONDITIONS[LS]: ' + str(conditions))

            data_point = DataPoint.objects.exclude(conditions).first()

#            print('DP: ' + str(data_point))

        seen_sources.sort()

#        print('GATHERED SOURCES: ' + json.dumps(seen_sources, indent=2))

        sources.value = json.dumps(seen_sources, indent=2)

        sources.save()

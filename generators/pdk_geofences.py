# pylint: disable=line-too-long, no-member

import datetime

import collections
import re

from django.contrib.gis.geos import GEOSGeometry
from django.template.loader import render_to_string
from django.utils import timezone

from passive_data_kit.models import DataPoint

def generator_name(identifier): # pylint: disable=unused-argument
    return 'Geofence Events'

def extract_secondary_identifier(properties):
    if 'transition' in properties:
        return properties['transition']

    return None

def extract_value(pattern, properties):
    for key, value in properties.iteritems():

        match = re.search(pattern, key)

        if match:
            return float(value)
        elif isinstance(value, collections.Mapping):
            found_value = extract_value(pattern, value)

            if found_value is not None:
                return found_value

    return None

def extract_location(point):
    properties = point.fetch_properties()

    latitude = extract_value('.*latitude.*', properties)
    longitude = extract_value('.*longitude.*', properties)

    if latitude is not None and longitude is not None:
        point.generated_at = GEOSGeometry('POINT(' + str(longitude) + ' ' + str(latitude) + ')')
        point.save()

def data_table(source, generator):
    context = {}
    context['source'] = source
    context['generator_identifier'] = generator

    start = timezone.now() - datetime.timedelta(days=7)

    context['values'] = DataPoint.objects.filter(source=source.identifier, generator_identifier=generator, created__gte=start).order_by('-created')

    return render_to_string('generators/pdk_geofence_event_table_template.html', context)

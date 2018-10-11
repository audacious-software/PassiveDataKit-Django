# pylint: disable=line-too-long, no-member

import calendar
import datetime
import json

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

def generator_name(identifier): # pylint: disable=unused-argument
    return 'Data Frequency'

def compile_visualization(identifier, points, folder): # pylint: disable=unused-argument
    now = timezone.now()

    now = now.replace(second=0, microsecond=0)

    remainder = now.minute % 10

    now = now.replace(minute=(now.minute - remainder))

    start = now - datetime.timedelta(days=2)

    points = points.filter(created__lte=now, created__gte=start)

    end = start + datetime.timedelta(seconds=600)

    timestamp_counts = {}

    keys = []

    while start < now:
        timestamp = str(calendar.timegm(start.timetuple()))

        keys.append(timestamp)

        timestamp_counts[timestamp] = points.filter(created__lte=end, created__gte=start).count()

        start = end
        end = start + datetime.timedelta(seconds=600)

    timestamp_counts['keys'] = keys

    with open(folder + '/timestamp-counts.json', 'w') as outfile:
        json.dump(timestamp_counts, outfile, indent=2)


def visualization(source, generator): # pylint: disable=unused-argument
    filename = settings.MEDIA_ROOT + '/pdk_visualizations/' + source.identifier + '/pdk-data-frequency/timestamp-counts.json'

    context = {}

    try:
        with open(filename) as infile:
            data = json.load(infile)

            context['data'] = data
    except IOError:
        context['data'] = {}

    return render_to_string('pdk_data_frequency_template.html', context)

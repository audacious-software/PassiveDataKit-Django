# pylint: disable=line-too-long, no-member

import calendar
import csv
import importlib
import json
import tempfile

from django.template.loader import render_to_string

from .models import DataPoint

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

def data_table(source, generator):
    try:
        generator_module = importlib.import_module('.generators.' + generator.replace('-', '_'), package='passive_data_kit')

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

def compile_report(generator, sources):
    try:
        generator_module = importlib.import_module('.generators.' + generator.replace('-', '_'), package='passive_data_kit')

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

        for source in sources:
            points = DataPoint.objects.filter(source=source, generator_identifier=generator).order_by('created') # pylint: disable=no-member,line-too-long

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
                    row.append(json.dumps(point.properties))

                    writer.writerow(row)

                index += 5000

    return filename

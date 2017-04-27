import calendar
import codecs
import csv
import json
import tempdir

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

# def viz_template(source, identifier):
#    if identifier == 'web-historian':
#        context = {
#           'source': source,
#           'identifier': identifier,
#        }
#        
#        return render_to_string('table_web_historian.html', context)
#    
#    return None

def compile_report(generator, sources):
    filename = tempfile.gettempdir() + '/pdk_' + generator + '.txt'
    
    with open(filename, 'w') as outfile:
        writer = csv.writer(outfile, delimiter='\t')
    
        writer.writerow(['Source', 'Generator', 'Generator Identifier', 'Created Timestamp', 'Created Date', 'Latitude', 'Longitude', 'Recorded Timestamp', 'Recorded Date', 'Properties'])
    
        for source in sources:
            points = DataPoint.objects.filter(source=source, generator_identifier=generator).order_by('created')
            
            index = 0
            count = points.count()
            
            while index < count:
#                print(source + '/' + generator + ': ' + str(index) + ' / ' + str(count))
#                
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

import datetime
import json

from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from django.contrib.admin.views.decorators import staff_member_required

from .models import DataPoint, DataBundle, DataSourceGroup, DataSource

@csrf_exempt
def add_data_point(request):
    response = { 'message': 'Data point added successfully.' }
      
    if request.method == 'CREATE':
        response = HttpResponse(json.dumps(response, indent=2), content_type='application/json', status=201)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'CREATE'
        response['Access-Control-Request-Headers'] = 'Content-Type'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        
        point = json.loads(request.body)
                
        point = DataPoint(recorded=timezone.now())
        point.source = point['passive-data-metadata']['source']
        point.generator = point['passive-data-metadata']['generator']
        point.created = datetime.datetime.fromtimestamp(point['passive-data-metadata']['source'], tz=timezone.get_default_timezone())
        point.properties = point
        
        point.save()

        return response
    elif request.method == 'OPTIONS':
        response = HttpResponse('', content_type='text/plain', status=200)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'CREATE'
        response['Access-Control-Request-Headers'] = 'Content-Type'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return response
    
    return HttpResponseNotAllowed(['CREATE'])


@csrf_exempt
def add_data_bundle(request):
    response = { 'message': 'Data bundle added successfully, and ready for processing.' }
     
    if request.method == 'CREATE':
        response = HttpResponse(json.dumps(response, indent=2), content_type='application/json', status=201)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'CREATE'
        response['Access-Control-Request-Headers'] = 'Content-Type'
        response['Access-Control-Allow-Headers'] = 'Content-Type'

        points = json.loads(request.body)
                
        bundle = DataBundle(recorded=timezone.now())
        bundle.properties = points
        bundle.save()
        
        return response
    elif request.method == 'OPTIONS':
        response = HttpResponse('', content_type='text/plain', status=200)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'CREATE'
        response['Access-Control-Request-Headers'] = 'Content-Type'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return response
    
    return HttpResponseNotAllowed(['CREATE'])

@staff_member_required
def pdk_home(request):
    c = RequestContext(request)
    
    if request.method == 'POST':
        if request.POST['operation'] == 'add_source':
            identifier = request.POST['source_identifier'].strip()
            name = request.POST['friendly_name'].strip()
        
            group = request.POST['assigned_group']
            group_name = request.POST['new_group_name'].strip()
        
            source = DataSource(identifier=identifier, name=name)
        
            if group == "-1":
                pass
            elif group == "0":
                group = DataSourceGroup.objects.filter(name=group_name).first()
                
                if group == None: 
                    group = DataSourceGroup(name=group_name)
                    group.save()
            
                source.group = group
            else:
                source.group = DataSourceGroup.objects.get(pk=int(group))
            
            source.save()
        if request.POST['operation'] == 'remove_source':
            DataSource.objects.filter(pk=int(request.POST['pk'])).delete()
    
    c['groups'] = DataSourceGroup.objects.order_by('name')
    c['solo_sources'] = DataSource.objects.filter(group=None).order_by('name')

    return render_to_response('pdk_home.html', c)

@staff_member_required
def unmatched_sources(request):
    sources = []
    
    for point in DataPoint.objects.order_by('source').values_list('source', flat=True).distinct():
        sources.append(point)

    return JsonResponse(sources, safe=False, json_dumps_params={'indent': 2})
    

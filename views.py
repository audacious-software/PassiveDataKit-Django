import json

from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import DataPoint

@csrf_exempt
def add_data_point(request):
    response = { 'message': 'Data point added successfully.' }
      
    if request.method == 'CREATE':
        response = HttpResponse(json.dumps(response, indent=2), content_type='application/json', status=201)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'CREATE'
        response['Access-Control-Request-Headers'] = 'Content-Type'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        
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
        
        return response
    elif request.method == 'OPTIONS':
        response = HttpResponse('', content_type='text/plain', status=200)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'CREATE'
        response['Access-Control-Request-Headers'] = 'Content-Type'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return response
    
    return HttpResponseNotAllowed(['CREATE'])


from django.shortcuts import render
from django.http import HttpResponseNotAllowed

from .models import DataPoint

def add_data_point(request):
    if request.method == 'CREATE':
        return HttpResponse(json.dumps(response, indent=2), content_type='application/json', status_code=201)
    
    return HttpResponseNotAllowed(['CREATE'])


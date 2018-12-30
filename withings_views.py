# pylint: disable=no-member, line-too-long

import calendar
import datetime
import importlib
import json
import os

import requests

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse, HttpResponseNotFound, \
                        FileResponse, UnreadablePostError
from django.shortcuts import render, get_object_or_404, redirect

from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from django.contrib.admin.views.decorators import staff_member_required

from .models import DataPoint, install_supports_jsonfield

AUTHORIZE_URL = 'https://account.withings.com/oauth2_user/authorize2'
ACCESS_TOKEN_URL = 'https://account.withings.com/oauth2/token'

@csrf_exempt
def pdk_withings_start(request, source_id):
    params = {
        'response_type': 'code',
        'client_id': settings.PDK_WITHINGS_CLIENT_ID,
        'state': source_id,
        'scope': ','.join(settings.PDK_WITHINGS_SCOPES),
        'redirect_uri': settings.PDK_WITHINGS_REDIRECT_URL,
    }
    
    return redirect(requests.Request('GET', AUTHORIZE_URL, params=params).prepare().url)


@csrf_exempt
def pdk_withings_auth(request):
    code = request.GET['code']
    source_id = request.GET['state']

    params = {
        'grant_type': 'authorization_code',
        'client_id': settings.PDK_WITHINGS_CLIENT_ID,
        'client_secret': settings.PDK_WITHINGS_SECRET,
        'code': code,
        'redirect_uri': settings.PDK_WITHINGS_REDIRECT_URL,
    }
    
    response = requests.post(ACCESS_TOKEN_URL, data=params)
    
    print('JSON: ' + json.dumps(response.json(), indent=2))
    
    point = DataPoint(source=source_id, generator='pdk-withings-server-auth', created=timezone.now())
    point.recorded = point.created
    point.generator_identifier = point.generator
    point.server_generated = True
    
    payload = response.json()
    
    payload['passive-data-metadata'] = {
        'source': source_id,
        'generator-id': point.generator_identifier,
        'generator': point.generator,
        'timestamp': calendar.timegm(point.created.timetuple())
    }

    if install_supports_jsonfield():
        point.properties = payload
    else:
        point.properties = json.dumps(payload, indent=2)
        
    point.save()

    return redirect('pdk_home')

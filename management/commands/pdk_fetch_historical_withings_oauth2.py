# -*- coding: utf-8 -*-
# pylint: disable=no-member, line-too-long

from __future__ import print_function

from builtins import str # pylint: disable=redefined-builtin

import calendar
import datetime
import json
import os
import time

import arrow
import requests

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from ...decorators import handle_lock
from ...models import DataPoint, install_supports_jsonfield

GENERATOR_NAME = 'pdk-withings-device: Passive Data Kit Server'

REFRESH_TOKEN_URL = 'https://account.withings.com/oauth2/token' # nosec

def refresh_access_token(properties):
    params = {
        'grant_type': 'refresh_token',
        'client_id': settings.PDK_WITHINGS_CLIENT_ID,
        'client_secret': settings.PDK_WITHINGS_SECRET,
        'refresh_token': properties['refresh_token'],
    }

    response = requests.post(REFRESH_TOKEN_URL, data=params)

    # print('REFRESH RESPONSE: ' + json.dumps(response.json(), indent=2))

    point = DataPoint(source=properties['passive-data-metadata']['source'], generator='pdk-withings-server-auth', created=timezone.now())
    point.recorded = point.created
    point.generator_identifier = point.generator
    point.server_generated = True

    payload = response.json()

    payload['passive-data-metadata'] = {
        'source': properties['passive-data-metadata']['source'],
        'generator-id': point.generator_identifier,
        'generator': point.generator,
        'timestamp': calendar.timegm(point.created.timetuple())
    }

    if install_supports_jsonfield():
        point.properties = payload
    else:
        point.properties = json.dumps(payload, indent=2)

    point.save()

    return payload['access_token']

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--source',
                            type=str,
                            dest='source',
                            default='all',
                            help='Specific source to fetch')

        parser.add_argument('--start',
                            type=str,
                            dest='start',
                            help='Start of date range to retrieve Withings data in format YYYY-MM-DD')

        parser.add_argument('--end',
                            type=str,
                            dest='end',
                            help='End of date range to retrieve Withings data in format YYYY-MM-DD')

    @handle_lock
    def handle(self, *args, **options): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        os.umask(000)

        start = options['start']
        if start is None:
            start = (timezone.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        end = options['end']

        if end is None:
            end = timezone.now().strftime('%Y-%m-%d')

        start_date = arrow.get(start).replace(hour=0, minute=0, second=0).to(settings.TIME_ZONE)
        end_date = arrow.get(end).replace(hour=0, minute=0, second=0).to(settings.TIME_ZONE)

        redo_dates = []

        sources = []

        if options['source'] != 'all':
            sources.append(options['source'])
        else:
            sources = DataPoint.objects.filter(generator_identifier='pdk-withings-server-auth').order_by('source').values_list('source', flat=True).distinct()

        for source in sources: # pylint: disable=too-many-nested-blocks
            data_point = DataPoint.objects.filter(source=source, generator_identifier='pdk-withings-server-auth').order_by('-created').first()

            if data_point is not None:
                properties = data_point.fetch_properties()

                try:
                    access_token = refresh_access_token(properties)

                    index_date = start_date

                    while index_date < end_date:
                        next_day = index_date.replace(days=+1)

                        try:
                            if options['source'] != 'all':
                                print('FETCHING INTRADAY FOR ' + source + ': ' + str(index_date) + ': ' + str(next_day))

                            fetch_intraday(data_point.source, access_token, index_date, next_day)

                            time.sleep(1)

                            if options['source'] != 'all':
                                print('FETCHING SLEEP MEASURES FOR ' + source + ': ' + str(index_date) + ': ' + str(next_day))

                            fetch_sleep_measures(data_point.source, access_token, index_date, next_day)

                            time.sleep(1)
                        except requests.exceptions.ReadTimeout:
                            problem_date = index_date.date()

                            if (problem_date in redo_dates) is False:
                                redo_dates.append(problem_date)

                        index_date = next_day
                except KeyError:
                    print('Error fetching data: ' + json.dumps(properties, indent=2))

        for redo_date in redo_dates:
            if options['source'] != 'all':
                print('REDO DATE: ' + str(redo_date))


def fetch_intraday(user_id, access_token, start_date, end_date): # pylint: disable=too-many-locals, too-many-statements, too-many-branches
    api_url = 'https://wbsapi.withings.net/v2/measure'

    params = {
        'action': 'getintradayactivity',
        'access_token': access_token,
        'startdate': str(start_date.timestamp),
        'enddate': str(end_date.timestamp)
    }

    response = requests.get(api_url, params=params, timeout=30)

    results = response.json()

    if 'body' in results and 'series' in results['body']:
        if results['body']['series'] == []:
            return

        for timestamp, values in list(results['body']['series'].items()):
            found = False

            created_date = arrow.get(timestamp).datetime

            matches = DataPoint.objects.filter(source=user_id, generator_identifier='pdk-withings-device', created=created_date)

            for match in matches:
                match_props = match.fetch_properties()

                if match_props['datastream'] == 'intraday-activity':
                    found = True

            if found is False:
                now = arrow.utcnow()

                new_point = DataPoint(source=user_id, generator=GENERATOR_NAME, generator_identifier='pdk-withings-device')

                new_point.created = created_date
                new_point.recorded = now.datetime

                new_properties = {}
                new_properties['datastream'] = 'intraday-activity'

                new_properties['activity_start'] = int(timestamp)
                new_properties['activity_duration'] = values['duration']

                if 'calories' in values:
                    new_properties['calories'] = values['calories']

                if 'distance' in values:
                    new_properties['distance'] = values['distance']

                if 'steps' in values:
                    new_properties['steps'] = values['steps']

                if 'elevation' in values:
                    new_properties['elevation_climbed'] = values['elevation']

                if 'sleep_state' in values:
                    new_properties['sleep_state'] = values['sleep_state']

                new_properties['observed'] = now.timestamp * 1000
                new_properties['server_fetched'] = True

                pdk_metadata = {}
                pdk_metadata['source'] = user_id
                pdk_metadata['generator-id'] = 'pdk-withings-device'
                pdk_metadata['generator'] = GENERATOR_NAME
                pdk_metadata['timestamp'] = now.timestamp

                new_properties['passive-data-metadata'] = pdk_metadata

                if install_supports_jsonfield():
                    new_point.properties = new_properties
                else:
                    new_point.properties = json.dumps(new_properties, indent=2)

                new_point.fetch_secondary_identifier()

                new_point.save()


def fetch_sleep_measures(user_id, access_token, start_date, end_date): # pylint: disable=too-many-locals, too-many-statements, too-many-branches
    api_url = 'https://wbsapi.withings.net/v2/sleep'

    params = {
        'action': 'get',
        'access_token': access_token,
        'startdate': str(start_date.timestamp),
        'enddate': str(end_date.timestamp)
    }

    response = requests.get(api_url, params=params, timeout=30)

    results = response.json()

    if 'body' in results and 'series' in results['body']:
        if results['body']['series'] == []:
            return

        for item in results['body']['series']:
            found = False

            created_date = arrow.get(item['enddate']).datetime

            matches = DataPoint.objects.filter(source=user_id, generator_identifier='pdk-withings-device', created=created_date)

            for match in matches:
                match_props = match.fetch_properties()

                if match_props['datastream'] == 'sleep-measures' and match_props['start_date'] == item['startdate']:
                    found = True

            if found is False:
                now = arrow.utcnow()

                new_point = DataPoint(source=user_id, generator=GENERATOR_NAME, generator_identifier='pdk-withings-device')

                new_point.created = created_date
                new_point.recorded = now.datetime

                new_properties = {}
                new_properties['datastream'] = 'sleep-measures'

                new_properties['start_date'] = item['startdate']
                new_properties['end_date'] = item['startdate']

                if item['state'] == 0:
                    new_properties['state'] = 'awake'
                elif item['state'] == 1:
                    new_properties['state'] = 'light-sleep'
                elif item['state'] == 2:
                    new_properties['state'] = 'deep-sleep'
                elif item['state'] == 3:
                    new_properties['state'] = 'rem-sleep'
                else:
                    new_properties['state'] = 'unknown'

                if results['body']['model'] == 32:
                    new_properties['measurement_device'] = 'aura'
                elif results['body']['model'] == 16:
                    new_properties['measurement_device'] = 'activity-tracker'
                else:
                    new_properties['measurement_device'] = 'unknown'

                new_properties['observed'] = now.timestamp * 1000
                new_properties['server_fetched'] = True

                pdk_metadata = {}
                pdk_metadata['source'] = user_id
                pdk_metadata['generator-id'] = 'pdk-withings-device'
                pdk_metadata['generator'] = GENERATOR_NAME
                pdk_metadata['timestamp'] = now.timestamp

                new_properties['passive-data-metadata'] = pdk_metadata

                if install_supports_jsonfield():
                    new_point.properties = new_properties
                else:
                    new_point.properties = json.dumps(new_properties, indent=2)

                new_point.fetch_secondary_identifier()

                new_point.save()
#            else:
#                print('SKIPPING ' + str(created_date))

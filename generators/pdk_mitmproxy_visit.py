# pylint: disable=line-too-long, no-member

import calendar
import csv
import datetime
import json
import tempfile
import time
import urlparse

import pytz

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from ..models import DataPoint, install_supports_jsonfield

def generator_name(identifier): # pylint: disable=unused-argument
    return 'PDK mitmproxy Web Visits'

def extract_secondary_identifier(properties):
    if 'url' in properties:
        url = urlparse.urlparse(properties['url'])
        
        return url.netloc

    return None

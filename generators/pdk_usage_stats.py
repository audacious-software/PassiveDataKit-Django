# pylint: disable=line-too-long, no-member

from __future__ import division

from builtins import str # pylint: disable=redefined-builtin

import calendar
import csv
import datetime
import io
import json
import os
import tempfile
import time

from zipfile import ZipFile

from past.utils import old_div

import arrow
import pytz
import requests

from bs4 import BeautifulSoup

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify

from ..models import DataPoint, DataSourceReference, DataGeneratorDefinition, DataServerMetadatum

def extract_secondary_identifier(properties):
    if 'event_type' in properties:
        return properties['event_type']

    return None

def generator_name(identifier): # pylint: disable=unused-argument
    return 'Device Usage Events'

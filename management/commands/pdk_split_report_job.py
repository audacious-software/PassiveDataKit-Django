# -*- coding: utf-8 -*-
# pylint: disable=no-member,line-too-long

from __future__ import print_function
from builtins import str
import copy
import json
import os

from django.core.management.base import BaseCommand

from ...decorators import handle_lock
from ...models import ReportJob, install_supports_jsonfield

class Command(BaseCommand):
    help = 'Splits existing jobs into two new jobs.'

    def add_arguments(self, parser):
        parser.add_argument('--pk',
                            type=int,
                            dest='pk',
                            default=None,
                            help='PK of the job to split')

    @handle_lock
    def handle(self, *args, **options): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        os.umask(000)

        report = ReportJob.objects.get(pk=options['pk'])

        new_report = ReportJob(requester=report.requester, requested=report.requested)
        new_report.sequence_index = report.sequence_index
        new_report.sequence_count = report.sequence_count

        if install_supports_jsonfield():
            parameters = report.parameters
        else:
            parameters = json.loads(report.parameters)

        new_sources = []
        old_sources = []

        index = 0

        print('Original sources: ' + str(len(parameters['sources'])))

        for source in parameters['sources']:
            if (index % 2) == 1:
                new_sources.append(source)
            else:
                old_sources.append(source)

            index += 1

        parameters['sources'] = old_sources

        new_parameters = copy.deepcopy(parameters)

        new_parameters['sources'] = new_sources

        print('Updated sources: ' + str(len(parameters['sources'])))
        print('New sources: ' + str(len(new_parameters['sources'])))

        if install_supports_jsonfield():
            report.parameters = parameters
            new_report.parameters = new_parameters
        else:
            report.parameters = json.dumps(parameters, indent=2)
            new_report.parameters = json.dumps(new_parameters, indent=2)

        report.save()
        new_report.save()

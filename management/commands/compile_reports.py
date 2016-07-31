 # -*- coding: utf-8 -*-

import datetime
import json
import os
import pytz
import traceback

import importlib

from zipfile import ZipFile

from django.conf import settings
from django.core.files import File
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from django.template.loader import render_to_string
from django.utils import timezone

from passive_data_kit.decorators import handle_lock
from passive_data_kit.models import DataPoint, DataBundle, DataPointVisualizations, ReportJob

class Command(BaseCommand):
    help = 'Compiles data reports requested by end users.'

    def add_arguments(self, parser):
        pass
#        parser.add_argument('--delete',
#            action='store_true',
#            dest='delete',
#            default=False,
#            help='Delete data bundles after processing')
#
#        parser.add_argument('--count', 
#            type=int, 
#            dest='bundle_count',
#            default=100,
#            help='Number of bundles to process in a single run')
    
    @handle_lock
    def handle(self, *args, **options):
        os.umask(000)
        
        report = ReportJob.objects.filter(started=None, completed=None).order_by('requested').first()
        
        if report is not None:
            report.started = timezone.now()
            report.save()
            
            sources = report.parameters['sources']
            generators = report.parameters['generators']
            
            filename = '/tmp/pdk_export_' + str(report.pk) + '.zip'

            with ZipFile(filename, 'w') as export_file:
                for generator in generators:
                    output_file = None
                
                    for app in settings.INSTALLED_APPS:
                        if output_file is None:
                            try:
                                pdk_api = importlib.import_module(app + '.pdk_api')

                                output_file = pdk_api.compile_report(generator, sources)
                            except ImportError:
                                traceback.print_exc()
                                output_file = None
                            except AttributeError:
                                traceback.print_exc()
                                output_file = None                                
                                
                    if output_file is not None:
                        export_file.write(output_file, output_file.split('/')[-1])
                        
                        os.remove(output_file)
                        
                export_file.close()
                
            report.report.save(filename.split('/')[-1], File(open(filename, 'r')))
            report.completed = timezone.now()
            report.save()
            
            subject = render_to_string('pdk_report_subject.txt', {'report': report, 'url': settings.SITE_URL})
            message = render_to_string('pdk_report_message.txt', {'report': report, 'url': settings.SITE_URL})
            
            host = settings.SITE_URL.split('/')[-2]

            send_mail(subject, message, 'Petey Kay <noreply@' + host + '>', [report.requester.email], fail_silently=False)
            

                            
                
            

# pylint: disable=no-member, line-too-long

import datetime
import importlib
import json
import os

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse, HttpResponseNotFound, \
                        FileResponse, UnreadablePostError
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from django.contrib.admin.views.decorators import staff_member_required

from .models import DataPoint, DataBundle, DataFile, DataSourceGroup, DataSource, ReportJob, \
                    generator_label, install_supports_jsonfield, DataSourceAlert, \
                    DataServerMetadatum


@csrf_exempt
def pdk_add_data_point(request):
    response = {'message': 'Data point added successfully.'}

    if request.method == 'CREATE':
        response = HttpResponse(json.dumps(response, indent=2), content_type='application/json', \
                                status=201)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'CREATE, POST'
        response['Access-Control-Request-Headers'] = 'Content-Type'
        response['Access-Control-Allow-Headers'] = 'Content-Type'

        point = json.loads(request.body)

        data_point = DataPoint(recorded=timezone.now())
        data_point.source = point['passive-data-metadata']['source']
        data_point.generator = point['passive-data-metadata']['generator']
        data_point.created = datetime.datetime.fromtimestamp(point['passive-data-metadata']['source'], tz=timezone.get_default_timezone()) # pylint: disable=line-too-long

        if install_supports_jsonfield():
            data_point.properties = point
        else:
            data_point.properties = json.dumps(point, indent=2)

        data_point.save()

        return response
    elif request.method == 'POST':
        response = HttpResponse(json.dumps(response, indent=2), \
                                content_type='application/json', \
                                status=201)

        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'CREATE, POST'
        response['Access-Control-Request-Headers'] = 'Content-Type'
        response['Access-Control-Allow-Headers'] = 'Content-Type'

        point = json.loads(request.POST['payload'])

        data_point = DataPoint(recorded=timezone.now())
        data_point.source = point['passive-data-metadata']['source']
        data_point.generator = point['passive-data-metadata']['generator']
        data_point.created = datetime.datetime.fromtimestamp(point['passive-data-metadata']['source'], tz=timezone.get_default_timezone()) # pylint: disable=line-too-long

        if install_supports_jsonfield():
            data_point.properties = point
        else:
            data_point.properties = json.dumps(point, indent=2)

        data_point.save()

        return response
    elif request.method == 'OPTIONS':
        response = HttpResponse('', content_type='text/plain', status=200)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'CREATE, POST'
        response['Access-Control-Request-Headers'] = 'Content-Type'
        response['Access-Control-Allow-Headers'] = 'Content-Type'

        return response

    return HttpResponseNotAllowed(['CREATE', 'POST'])


@csrf_exempt
def pdk_add_data_bundle(request): # pylint: disable=too-many-statements
    response = {'message': 'Data bundle added successfully, and ready for processing.'}

    if request.method == 'CREATE':
        response = HttpResponse(json.dumps(response, indent=2), \
                                content_type='application/json', \
                                status=201)

        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'CREATE, POST, HEAD'
        response['Access-Control-Request-Headers'] = 'Content-Type'
        response['Access-Control-Allow-Headers'] = 'Content-Type'

        points = None

        try:
            points = json.loads(request.body)
        except UnreadablePostError:
            response = {'message': 'Unable to parse data bundle.'}
            response = HttpResponse(json.dumps(response, indent=2), \
                                    content_type='application/json', \
                                    status=400)

            return response

        bundle = DataBundle(recorded=timezone.now())

        if install_supports_jsonfield():
            bundle.properties = points
        else:
            bundle.properties = json.dumps(points, indent=2)

        bundle.save()

        return response

    elif request.method == 'POST':
        response = HttpResponse(json.dumps(response, indent=2), \
                                content_type='application/json', \
                                status=201)

        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'CREATE, POST, HEAD'
        response['Access-Control-Request-Headers'] = 'Content-Type'
        response['Access-Control-Allow-Headers'] = 'Content-Type'

        try:
            points = json.loads(request.POST['payload'])

            bundle = DataBundle(recorded=timezone.now())

            if install_supports_jsonfield():
                bundle.properties = points
            else:
                bundle.properties = json.dumps(points, indent=2)

            bundle.save()
        except ValueError:
            response = {'message': 'Unable to parse data bundle.'}
            response = HttpResponse(json.dumps(response, indent=2), \
                                    content_type='application/json', \
                                    status=400)
        except UnreadablePostError:
            response = {'message': 'Unable to parse data bundle.'}
            response = HttpResponse(json.dumps(response, indent=2), \
                                    content_type='application/json', \
                                    status=400)

        for key, value in request.FILES.iteritems(): # pylint: disable=unused-variable
            data_file = DataFile(data_bundle=bundle)
            data_file.identifier = value.name
            data_file.content_type = value.content_type
            data_file.content_file.save(value.name, value)
            data_file.save()

        return response
    elif request.method == 'OPTIONS':
        response = HttpResponse('', content_type='text/plain', status=200)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'CREATE, POST, HEAD'
        response['Access-Control-Request-Headers'] = 'Content-Type'
        response['Access-Control-Allow-Headers'] = 'Content-Type'

        return response
    elif request.method == 'HEAD':
        response = HttpResponse('', content_type='text/plain', status=200)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'CREATE, POST, HEAD'
        response['Access-Control-Request-Headers'] = 'Content-Type'
        response['Access-Control-Allow-Headers'] = 'Content-Type'

        return response


    return HttpResponseNotAllowed(['CREATE', 'POST', 'HEAD'])


@staff_member_required
def pdk_home(request): # pylint: disable=too-many-branches, too-many-statements
    for app in settings.INSTALLED_APPS:
        try:
            app_views = importlib.import_module(app + '.views')

            return app_views.custom_pdk_home(request)
        except ImportError:
            pass
        except AttributeError:
            pass

    context = {}

    if request.method == 'POST':
        if request.POST['operation'] == 'add_source':
            identifier = request.POST['source_identifier'].strip()
            name = request.POST['friendly_name'].strip()

            group = request.POST['assigned_group']
            group_name = request.POST['new_group_name'].strip()

            final_identifier = identifier
            final_count = 2

            while DataSource.objects.filter(identifier=final_identifier).count() > 0:
                final_identifier = identifier + '-' + str(final_count)

                final_count += 1

            final_name = name
            final_count = 2

            while DataSource.objects.filter(name=final_name).count() > 0:
                final_name = name + ' ' + str(final_count)

                final_count += 1

            source = DataSource(identifier=final_identifier, name=final_name)

            if group == "-1":
                pass
            elif group == "0":
                group = DataSourceGroup.objects.filter(name=group_name).first()

                if group is None:
                    group = DataSourceGroup(name=group_name)
                    group.save()

                source.group = group
            else:
                source.group = DataSourceGroup.objects.get(pk=int(group))

            source.save()
        elif request.POST['operation'] == 'remove_source':
            DataSource.objects.filter(pk=int(request.POST['pk'])).delete()
        elif request.POST['operation'] == 'move_source':
            source = DataSource.objects.get(pk=int(request.POST['move_pk']))

            group_pk = int(request.POST['move_group_pk'])
            group_name = request.POST['move_group_name']

            if group_pk == 0 and group_name.strip() != '':
                group = DataSourceGroup.objects.filter(name=group_name).first()

                if group is None:
                    group = DataSourceGroup(name=group_name)
                    group.save()

                source.group = group
            else:
                source.group = DataSourceGroup.objects.get(pk=group_pk)

            source.save()
        elif request.POST['operation'] == 'rename_source':
            source = DataSource.objects.get(pk=int(request.POST['rename_pk']))
            source.name = request.POST['rename_name']

            source.save()

    context['groups'] = DataSourceGroup.objects.order_by('name')
    context['solo_sources'] = DataSource.objects.filter(group=None).order_by('name')

    return render(request, 'pdk_home.html', context=context)


@staff_member_required
def pdk_source(request, source_id): # pylint: disable=unused-argument
    context = {}

    source = DataSource.objects.filter(identifier=source_id).first()

    if source is None:
        source = DataSource(identifier=source_id, name='Unknown')
        source.save()

    context['source'] = source

    context['alerts'] = DataSourceAlert.objects.filter(active=True, data_source=source)

    return render(request, 'pdk_source.html', context=context)


@staff_member_required
def pdk_source_generator(request, source_id, generator_id): # pylint: disable=unused-argument
    context = {}

    source = DataSource.objects.filter(identifier=source_id).first()

    if source is None:
        source = DataSource(identifier=source_id, name='Unknown')
        source.save()

    context['source'] = source
    context['generator'] = generator_id
    context['generator_label'] = generator_label(generator_id)

    context['visualization'] = None

    for app in settings.INSTALLED_APPS:
        if context['visualization'] is None:
            try:
                pdk_api = importlib.import_module(app + '.pdk_api')

                context['visualization'] = pdk_api.visualization(source, generator_id)
            except ImportError:
                pass
            except AttributeError:
                pass

    for app in settings.INSTALLED_APPS:
        try:
            pdk_api = importlib.import_module(app + '.pdk_api')

            context['data_table'] = pdk_api.data_table(source, generator_id)
        except ImportError:
            pass
        except AttributeError:
            pass

    return render(request, 'pdk_source_generator.html', context=context)


@staff_member_required
def pdk_unmatched_sources(request): # pylint: disable=unused-argument
    sources = DataPoint.objects.sources()

#    for point in DataPoint.objects.order_by('source').values_list('source', flat=True).distinct():
#        sources.append(point)

    return JsonResponse(sources, safe=False, json_dumps_params={'indent': 2})


@staff_member_required
def pdk_visualization_data(request, source_id, generator_id, page): # pylint: disable=unused-argument
    folder = settings.MEDIA_ROOT + '/pdk_visualizations/' + source_id + '/' + generator_id

    filename = 'visualization-' + page + '.json'

    if page == '0':
        filename = 'visualization.json'

    try:
        with open(folder + '/' + filename) as data_file:
            return HttpResponse(data_file.read(), content_type='application/json')
    except IOError:
        pass

    return HttpResponseNotFound()


@staff_member_required
def pdk_download_report(request, report_id): # pylint: disable=unused-argument
    job = get_object_or_404(ReportJob, pk=int(report_id))

    filename = settings.MEDIA_ROOT + '/' + job.report.name

    response = FileResponse(open(filename, 'rb'), content_type='application/octet-stream')

    download_name = 'pdk-export_' + job.started.date().isoformat() + '_' + str(job.pk) + '.zip'

    response['Content-Length'] = os.path.getsize(filename)
    response['Content-Disposition'] = 'attachment; filename=' + download_name

    return response


@staff_member_required
def pdk_export(request): # pylint: disable=too-many-branches, too-many-locals, too-many-statements
    context = {}

    context['sources'] = sorted(DataPoint.objects.sources())
    context['generators'] = sorted(DataPoint.objects.generator_identifiers())

    to_remove = []

    for generator in context['generators']:
        if generator in context['sources']:
            context['sources'].remove(generator)

        try:
            if generator in settings.PDK_EXCLUDE_GENERATORS:
                to_remove.append(generator)
        except AttributeError:
            pass

    for generator in to_remove:
        context['generators'].remove(generator)

    all_extra_generators = []
    to_remove = []
    
    try:
    	for extra_generator in settings.PDK_EXTRA_GENERATORS:
    		all_extra_generators.append(extra_generator) 
    except AttributeError:
    	pass

    for app in settings.INSTALLED_APPS: # pylint: disable=too-many-nested-blocks
        for generator in context['generators']:
            try:
                module_name = '.generators.' + generator.replace('-', '_')

                generator_module = importlib.import_module(module_name, package=app)

                extra_generators = generator_module.extra_generators(generator)

                if extra_generators is not None and extra_generators:
                    for extra_generator in extra_generators:
                        all_extra_generators.append(extra_generator)

                        try:
                            if extra_generator[0] in settings.PDK_EXCLUDE_GENERATORS:
                                to_remove.append(extra_generator)
                        except AttributeError:
                            pass

            except ImportError:
                pass

            except AttributeError:
                pass

    for generator in to_remove:
        all_extra_generators.remove(generator)

    context['extra_generators'] = all_extra_generators

    context['message'] = ''
    context['message_type'] = 'ok'

    if request.method == 'POST':
        export_sources = []
        export_generators = []

        for source in context['sources']:
            key = 'source_' + source

            if key in request.POST:
                export_sources.append(source)

        for generator in context['generators']:
            key = 'generator_' + generator

            if key in request.POST:
                export_generators.append(generator)

        for generator in context['extra_generators']:
            key = 'generator_' + generator[0]

            if key in request.POST:
                export_generators.append(generator[0])

        if len(export_sources) == 0: # pylint: disable=len-as-condition
            context['message_type'] = 'error'

            if len(export_generators) == 0: # pylint: disable=len-as-condition
                context['message'] = 'Please select one or more sources and generators to export data.' # pylint: disable=line-too-long
            else:
                context['message'] = 'Please select one or more sources to export data.'
        elif len(export_generators) == 0: # pylint: disable=len-as-condition
            context['message_type'] = 'error'

            context['message'] = 'Please select one or more generators to export data.'
        else:
            export_raw = ('export_raw_json' in request.POST and request.POST['export_raw_json'])

            data_start = request.POST['data_start']

            data_end = request.POST['data_end']

            created = ReportJob.objects.create_jobs(request.user, export_sources, export_generators, export_raw, data_start, data_end)

            context['message_type'] = 'ok'

            if created == 1:
                context['message'] = 'Export job queued. Check your e-mail for a link to the output when the export is complete.' # pylint: disable=line-too-long
            else:
                context['message'] = 'Export jobs queued. Check your e-mail for links to the output when the export is complete.' # pylint: disable=line-too-long

    return render(request, 'pdk_export.html', context=context)


@staff_member_required
def pdk_system_health(request):
    datum = DataServerMetadatum.objects.filter(key='Server Health').first()

    if datum is not None:
        return render(request, 'pdk_system_health.html', context=json.loads(datum.value))

    return render(request, 'pdk_system_health.html', context={})


@staff_member_required
def pdk_profile(request):
    context = {}
    context['user'] = request.user

    if request.method == 'POST':
        current_password = request.POST['current_password']

        if request.user.check_password(current_password):
            new_password = request.POST['new_password']
            confirm_password = request.POST['confirm_password']

            if new_password == confirm_password:
                request.user.set_password(new_password)
                request.user.save()

                context['message'] = 'Password updated successfully.'
                context['message_class'] = 'success'
            else:
                context['message'] = 'Provided passwords do not match. Please try again.'
                context['message_class'] = 'danger'
        else:
            context['message'] = 'Current password is incorrect. Please try again.'
            context['message_class'] = 'danger'

    return render(request, 'pdk_user_profile.html', context=context)

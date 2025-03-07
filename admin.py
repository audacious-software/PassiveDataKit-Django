# pylint: disable=no-member, line-too-long, wrong-import-position

import datetime
import sys

from prettyjson import PrettyJSONWidget

from django.contrib.admin import SimpleListFilter
from django.contrib.gis import admin

if sys.version_info[0] > 2:
    from django.db.models import JSONField # pylint: disable=no-name-in-module
else:
    from django.contrib.postgres.fields import JSONField

from .models import DataPoint, DataBundle, DataSource, DataSourceGroup, \
                    DataPointVisualization, ReportJob, DataSourceAlert, \
                    DataServerMetadatum, ReportJobBatchRequest, DataServerApiToken, \
                    DataFile, AppConfiguration, DataGeneratorDefinition, \
                    DataSourceReference, ReportDestination, DataServerAccessRequest, \
                    DataServerAccessRequestPending, DeviceModel, Device, DeviceIssue, \
                    DataServer

def reset_visualizations(modeladmin, request, queryset): # pylint: disable=unused-argument
    for visualization in queryset:
        visualization.last_updated = datetime.datetime.min

        visualization.save()

reset_visualizations.description = 'Reset visualizations'

@admin.register(DataPointVisualization)
class DataPointVisualizationAdmin(admin.OSMGeoAdmin):
    list_display = ('source', 'generator_identifier', 'last_updated',)
    list_filter = ('source', 'generator_identifier', 'last_updated',)

    actions = [reset_visualizations]

class DataPointGeneratorIdentifierFilter(SimpleListFilter):
    title = 'Generator'
    parameter_name = 'generator_definition'

    def lookups(self, request, model_admin):
        values = []

        for generator_definition in DataGeneratorDefinition.objects.all().order_by('name'):
            values.append((generator_definition.pk, generator_definition.name,))

        return values

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(generator_definition=self.value())

        return None


class DataPointSourceFilter(SimpleListFilter):
    title = 'Source'
    parameter_name = 'source_reference'

    def lookups(self, request, model_admin):
        values = []

        for reference in DataSourceReference.objects.all().order_by('source'):
            values.append((reference.pk, reference.source,))

        return values

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(source_reference=self.value())

        return None

class DataFileInline(admin.TabularInline):
    model = DataFile

    fields = ['content_file', 'identifier', 'content_type']

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None): # pylint: disable=arguments-differ,unused-argument
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(DataPoint)
class DataPointAdmin(admin.OSMGeoAdmin):
    openlayers_url = 'https://openlayers.org/api/2.13.1/OpenLayers.js'

    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget(attrs={'initial': 'parsed'})}
    }

    inlines = [
        DataFileInline,
    ]

    exclude = [
        'generated_at',
    ]

    list_display = (
        'source_reference',
        'generator_definition',
        'secondary_identifier',
        'file_count',
        'created',
        'recorded',
    )

    list_filter = (
        'created',
        'recorded',
        DataPointGeneratorIdentifierFilter,
        DataPointSourceFilter,
        )

    def file_count(self, obj): # pylint: disable=no-self-use
        return obj.data_files.all().count()

@admin.register(DataBundle)
class DataBundleAdmin(admin.OSMGeoAdmin):
    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget(attrs={'initial': 'parsed'})}
    }

    list_display = ('recorded', 'processed', 'errored', 'compression',)
    list_filter = ('processed', 'recorded', 'errored', 'compression',)

@admin.register(DataFile)
class DataFileAdmin(admin.OSMGeoAdmin):
    list_display = ('identifier', 'content_file', 'content_type', 'data_point', 'data_bundle',)
    list_filter = ('content_type',)
    readonly_fields = ['data_point', 'data_bundle']

@admin.register(DataSourceGroup)
class DataSourceGroupAdmin(admin.OSMGeoAdmin):
    list_display = ('name', 'suppress_alerts',)
    list_filter = ('suppress_alerts',)

def suppress_alerts(modeladmin, request, queryset): # pylint: disable=unused-argument
    queryset.update(suppress_alerts=True)

suppress_alerts.description = 'Suppress Alerts'

def enable_alerts(modeladmin, request, queryset): # pylint: disable=unused-argument
    queryset.update(suppress_alerts=False)

enable_alerts.description = 'Enable Alerts'

@admin.register(DataSource)
class DataSourceAdmin(admin.OSMGeoAdmin):
    list_display = ('name', 'identifier', 'group', 'suppress_alerts', 'server', 'performance_metadata_updated',)
    list_filter = ('group', 'suppress_alerts', 'performance_metadata_updated', 'configuration',)
    search_fields = ['name', 'identifier']

    actions = [enable_alerts, suppress_alerts]

def reset_report_jobs(modeladmin, request, queryset): # pylint: disable=unused-argument
    for job in queryset:
        job.started = None
        job.completed = None

        if job.report is not None:
            job.report.delete()
            job.report = None

        job.save()

reset_report_jobs.description = 'Reset report jobs'

@admin.register(ReportJob)
class ReportJobAdmin(admin.OSMGeoAdmin):
    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget(attrs={'initial': 'parsed'})}
    }

    list_display = (
        'requester',
        'requested',
        'sequence_index',
        'sequence_count',
        'priority',
        'started',
        'completed'
    )

    list_filter = ('requested', 'started', 'completed', 'priority',)

    actions = [reset_report_jobs]
    search_fields = ('parameters',)


@admin.register(ReportJobBatchRequest)
class ReportJobBatchRequestAdmin(admin.OSMGeoAdmin):
    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget(attrs={'initial': 'parsed'})}
    }

    list_display = ('requester', 'requested', 'priority', 'started', 'completed')
    list_filter = ('requested', 'started', 'completed', 'priority', 'requester')


@admin.register(DataServerMetadatum)
class DataServerMetadatumAdmin(admin.OSMGeoAdmin):
    list_display = ('key', 'last_updated',)
    list_filter = ('last_updated',)
    search_fields = ['key', 'value']


@admin.register(DataSourceAlert)
class DataSourceAlertAdmin(admin.OSMGeoAdmin):
    list_display = (
        'created',
        'updated',
        'data_source',
        'generator_identifier',
        'alert_name',
        'alert_level',
        'active'
    )

    list_filter = ('active', 'created', 'updated', 'alert_level', 'generator_identifier',)

@admin.register(DataServerApiToken)
class DataServerApiTokenAdmin(admin.OSMGeoAdmin):
    list_display = ('user', 'expires',)
    list_filter = ('expires', 'user',)

@admin.register(AppConfiguration)
class AppConfigurationAdmin(admin.OSMGeoAdmin):
    list_display = ('name', 'evaluate_order', 'id_pattern', 'context_pattern', 'is_valid', 'is_enabled',)
    search_fields = ('name', 'id_pattern', 'context_pattern', 'configuration_json',)

    list_filter = ('is_enabled', 'is_valid',)

    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget(attrs={'initial': 'parsed'})}
    }

@admin.register(DataGeneratorDefinition)
class DataGeneratorDefinitionAdmin(admin.OSMGeoAdmin):
    list_display = ('name', 'generator_identifier',)
    search_fields = ('name', 'generator_identifier', 'description',)

@admin.register(DataSourceReference)
class DataSourceReferenceAdmin(admin.OSMGeoAdmin):
    list_display = ('source',)
    search_fields = ('source',)

@admin.register(ReportDestination)
class ReportDestinationAdmin(admin.OSMGeoAdmin):
    list_display = ('user', 'destination', 'description')
    search_fields = ('destination', 'user',)

@admin.register(DataServerAccessRequestPending)
class DataServerAccessRequestPendingAdmin(admin.OSMGeoAdmin):
    list_display = ('user_identifier', 'request_type', 'request_time', 'successful', 'processed',)

    search_fields = ('user_identifier', 'request_metadata',)
    list_filter = ('request_time', 'request_type', 'successful', 'processed',)

@admin.register(DataServerAccessRequest)
class DataServerAccessRequestAdmin(admin.OSMGeoAdmin):
    list_display = ('user_identifier', 'request_type', 'request_time', 'successful',)

    search_fields = ('user_identifier', 'request_metadata',)
    list_filter = ('request_time', 'request_type', 'successful',)

@admin.register(DeviceModel)
class DeviceModelAdmin(admin.OSMGeoAdmin):
    list_display = ('model', 'manufacturer',)

    search_fields = ('model', 'manufacturer', 'reference', 'notes',)
    list_filter = ('manufacturer',)

@admin.register(Device)
class DeviceAdmin(admin.OSMGeoAdmin):
    list_display = ('source', 'model', 'platform',)

    search_fields = ('source__identifier', 'model__model', 'model__manufacturer', 'platform', 'notes',)
    list_filter = ('platform', 'model',)

@admin.register(DeviceIssue)
class DeviceIssueAdmin(admin.OSMGeoAdmin):
    list_display = ('device', 'state', 'created', 'last_updated',)

    search_fields = ('tags', 'description', 'user_agent')
    list_filter = ('state', 'created', 'last_updated', 'stability_related', 'uptime_related', 'responsiveness_related', 'battery_use_related', 'power_management_related', 'data_volume_related', 'data_quality_related', 'bandwidth_related', 'storage_related', 'configuration_related', 'location_related',)


@admin.register(DataServer)
class DataServerAdmin(admin.OSMGeoAdmin):
    list_display = ('name', 'upload_url', 'source_metadata_url',)

    search_fields = ('name', 'upload_url', 'source_metadata_url',)

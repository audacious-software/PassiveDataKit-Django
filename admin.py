# pylint: disable=no-member, line-too-long

import datetime
import json

from prettyjson import PrettyJSONWidget

from django.contrib.admin import SimpleListFilter
from django.contrib.gis import admin
from django.contrib.postgres.fields import JSONField

from .models import DataPoint, DataBundle, DataSource, DataSourceGroup, \
                    DataPointVisualization, ReportJob, DataSourceAlert, \
                    DataServerMetadatum, ReportJobBatchRequest, DataServerApiToken, \
                    DataFile, AppConfiguration

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
    title = 'Generator Identifier'
    parameter_name = 'generator_identifier'

    def lookups(self, request, model_admin):
        values = []

        identifiers = DataPoint.objects.generator_identifiers()

        if identifiers is not None:
            for identifier in identifiers:
                values.append((identifier, identifier,))

            return values

        DataPoint.objects.generator_identifiers()

        return self.lookups(request, model_admin)


    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(generator_identifier=self.value())

        return None


class DataPointSourceFilter(SimpleListFilter):
    title = 'Source'
    parameter_name = 'source'

    def lookups(self, request, model_admin):
        values = []

        sources = DataServerMetadatum.objects.filter(key="Data Point Sources").first()

        identifiers = DataServerMetadatum.objects.filter(key="Data Point Generators").first()

        seen_identifiers = []

        if identifiers is not None:
            seen_identifiers = json.loads(identifiers.value)

        if sources is not None:
            seen_sources = json.loads(sources.value)

            seen_sources.sort()

            for source in seen_sources:
                if (source in seen_identifiers) is False:
                    values.append((source, source,))

        return values

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(source=self.value())

        return None


@admin.register(DataPoint)
class DataPointAdmin(admin.OSMGeoAdmin):
    openlayers_url = 'https://openlayers.org/api/2.13.1/OpenLayers.js'

    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }

    list_display = (
        'source',
        'generator_identifier',
        'secondary_identifier',
        'created',
        'recorded',
    )

    list_filter = (
        'created',
        'recorded',
        DataPointGeneratorIdentifierFilter,
        DataPointSourceFilter,
        )

@admin.register(DataBundle)
class DataBundleAdmin(admin.OSMGeoAdmin):
    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }

    list_display = ('recorded', 'processed',)
    list_filter = ('processed', 'recorded',)

@admin.register(DataFile)
class DataFileAdmin(admin.OSMGeoAdmin):
    list_display = ('content_file', 'content_type', 'identifier', 'data_point', 'data_bundle',)
    list_filter = ('content_type',)

@admin.register(DataSourceGroup)
class DataSourceGroupAdmin(admin.OSMGeoAdmin):
    list_display = ('name', 'suppress_alerts',)
    list_filter = ('suppress_alerts',)

@admin.register(DataSource)
class DataSourceAdmin(admin.OSMGeoAdmin):
    list_display = ('name', 'identifier', 'group', 'suppress_alerts',)
    list_filter = ('group', 'suppress_alerts',)


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
    list_display = (
        'requester',
        'requested',
        'sequence_index',
        'sequence_count',
        'started',
        'completed'
    )

    list_filter = ('requested', 'started', 'completed',)

    actions = [reset_report_jobs]


@admin.register(ReportJobBatchRequest)
class ReportJobBatchRequestAdmin(admin.OSMGeoAdmin):
    list_display = ('requester', 'requested', 'started', 'completed')
    list_filter = ('requested', 'started', 'completed', 'requester')


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

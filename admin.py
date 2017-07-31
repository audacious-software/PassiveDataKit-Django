from django.contrib.gis import admin

from .models import DataPoint, DataBundle, DataSource, DataSourceGroup, \
                    DataPointVisualizations, ReportJob, DataSourceAlert

@admin.register(DataPointVisualizations)
class DataPointVisualizationsAdmin(admin.OSMGeoAdmin):
    list_display = ('source', 'generator_identifier', 'last_updated',)
    list_filter = ('source', 'generator_identifier', 'last_updated',)

@admin.register(DataPoint)
class DataPointAdmin(admin.OSMGeoAdmin):
    openlayers_url = 'https://openlayers.org/api/2.13.1/OpenLayers.js'

    list_display = ('source', 'generator_identifier', 'secondary_identifier', 'created', \
                    'recorded',)
    list_filter = (
        'created',
        'recorded',
        'generator_identifier',
        )

@admin.register(DataBundle)
class DataBundleAdmin(admin.OSMGeoAdmin):
    list_display = ('recorded', 'processed',)
    list_filter = ('processed', 'recorded',)

@admin.register(DataSourceGroup)
class DataSourceGroupAdmin(admin.OSMGeoAdmin):
    list_display = ('name',)

@admin.register(DataSource)
class DataSourceAdmin(admin.OSMGeoAdmin):
    list_display = ('name', 'identifier', 'group')
    list_filter = ('group',)


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
    list_display = ('requester', 'requested', 'started', 'completed')
    list_filter = ('requested', 'started', 'completed',)

    actions = [reset_report_jobs]

@admin.register(DataSourceAlert)
class DataSourceAlertAdmin(admin.OSMGeoAdmin):
    list_display = ('alert_name', 'data_source', 'generator_identifier', 'active', 'alert_level', \
                    'created', 'updated',)
    list_filter = ('active', 'alert_level', 'created', 'alert_name', 'generator_identifier', \
                   'data_source',)

from django.contrib import admin

from .models import DataPoint, DataBundle, DataSource, DataSourceGroup, \
                    DataPointVisualizations, ReportJob

@admin.register(DataPointVisualizations)
class DataPointVisualizationsAdmin(admin.ModelAdmin):
    list_display = ('source', 'generator_identifier', 'last_updated',)
    list_filter = ('source', 'generator_identifier', 'last_updated',)

@admin.register(DataPoint)
class DataPointAdmin(admin.ModelAdmin):
    list_display = ('source', 'generator_identifier', 'created', 'recorded',)
    list_filter = ('created', 'recorded', 'generator_identifier',)

@admin.register(DataBundle)
class DataBundleAdmin(admin.ModelAdmin):
    list_display = ('recorded', 'processed',)
    list_filter = ('processed', 'recorded',)

@admin.register(DataSourceGroup)
class DataBundleAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(DataSource)
class DataBundleAdmin(admin.ModelAdmin):
    list_display = ('name', 'identifier', 'group')
    list_filter = ('group',)

@admin.register(ReportJob)
class ReportJobAdmin(admin.ModelAdmin):
    list_display = ('requester', 'requested', 'started', 'completed')
    list_filter = ('requested', 'started', 'completed',)

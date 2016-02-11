from django.contrib import admin

from .models import DataPoint, DataBundle

@admin.register(DataPoint)
class DataPointAdmin(admin.ModelAdmin):
    list_display = ('source', 'created', 'recorded',)
    list_filter = ('created', 'generator', 'source')

@admin.register(DataBundle)
class DataBundleAdmin(admin.ModelAdmin):
    list_display = ('recorded', 'processed',)
    list_filter = ('processed', 'recorded',)

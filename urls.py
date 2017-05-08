# pylint: disable=line-too-long

from django.conf.urls import url

from django.conf import settings

from .views import add_data_point, add_data_bundle, pdk_home, unmatched_sources, pdk_source, \
                   pdk_source_generator, pdk_visualization_data, pdk_export, pdk_download_report

urlpatterns = [
    url(r'^add-point.json$', add_data_point, name='pdk_add_data_point'),
    url(r'^add-bundle.json$', add_data_bundle, name='pdk_add_data_bundle'),
]

try:
    if settings.PDK_DASHBOARD_ENABLED:
        urlpatterns.append(url(r'^visualization/(?P<source_id>.+)/(?P<generator_id>.+)/(?P<page>\d+).json$', \
                               pdk_visualization_data, name='pdk_visualization_data'))
        urlpatterns.append(url(r'^report/(?P<report_id>\d+)/download$', pdk_download_report, name='pdk_download_report'))
        urlpatterns.append(url(r'^source/(?P<source_id>.+)/(?P<generator_id>.+)$', pdk_source_generator, name='pdk_source_generator'))
        urlpatterns.append(url(r'^source/(?P<source_id>.+)$', pdk_source, name='pdk_source'))
        urlpatterns.append(url(r'^export$', pdk_export, name='pdk_export'))
        urlpatterns.append(url(r'^unmatched-sources.json$', unmatched_sources, name='pdk_unmatched_sources'))
        urlpatterns.append(url(r'^$', pdk_home, name='pdk_home'))
except AttributeError:
    pass

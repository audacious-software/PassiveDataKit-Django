from django.conf.urls import url

from .views import add_data_point, add_data_bundle, pdk_home, unmatched_sources, pdk_source, pdk_source_generator, pdk_visualization_data

urlpatterns = [
    url(r'^visualization/(?P<source_id>.+)/(?P<generator_id>.+)/(?P<page>\d+).json$', pdk_visualization_data, name='pdk_visualization_data'),
    url(r'^source/(?P<source_id>.+)/(?P<generator_id>.+)$', pdk_source_generator, name='pdk_source_generator'),
    url(r'^source/(?P<source_id>.+)$', pdk_source, name='pdk_source'),
    url(r'^add-point.json$', add_data_point, name='pdk_add_data_point'),
    url(r'^add-bundle.json$', add_data_bundle, name='pdk_add_data_bundle'),
    url(r'^unmatched-sources.json$', unmatched_sources, name='pdk_unmatched_sources'),
    url(r'^$', pdk_home, name='pdk_home'),
]

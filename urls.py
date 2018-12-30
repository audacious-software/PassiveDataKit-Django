# pylint: disable=line-too-long

from django.conf.urls import url
from django.contrib.auth.views import logout
from django.conf import settings

from .views import pdk_add_data_point, pdk_add_data_bundle, pdk_home, pdk_unmatched_sources, pdk_source, \
                   pdk_source_generator, pdk_visualization_data, pdk_export, pdk_download_report, \
                   pdk_system_health, pdk_profile

urlpatterns = [
    url(r'^add-point.json$', pdk_add_data_point, name='pdk_add_data_point'),
    url(r'^add-bundle.json$', pdk_add_data_bundle, name='pdk_add_data_bundle'),
]

try:
    from .withings_views import pdk_withings_start, pdk_withings_auth

    if settings.PDK_WITHINGS_CLIENT_ID and settings.PDK_WITHINGS_SECRET:
        urlpatterns.append(url(r'^withings/start/(?P<source_id>.+)$', pdk_withings_start, name='pdk_withings_start'))
        urlpatterns.append(url(r'^withings/auth$', pdk_withings_auth, name='pdk_withings_auth'))
except AttributeError:
    pass

try:
    if settings.PDK_DASHBOARD_ENABLED:
        urlpatterns.append(url(r'^visualization/(?P<source_id>.+)/(?P<generator_id>.+)/(?P<page>\d+).json$', \
                               pdk_visualization_data, name='pdk_visualization_data'))
        urlpatterns.append(url(r'^report/(?P<report_id>\d+)/download$', pdk_download_report, name='pdk_download_report'))
        urlpatterns.append(url(r'^source/(?P<source_id>.+)/(?P<generator_id>.+)$', pdk_source_generator, name='pdk_source_generator'))
        urlpatterns.append(url(r'^source/(?P<source_id>.+)$', pdk_source, name='pdk_source'))
        urlpatterns.append(url(r'^export$', pdk_export, name='pdk_export'))
        urlpatterns.append(url(r'^system-health$', pdk_system_health, name='pdk_system_health'))
        urlpatterns.append(url(r'^profile$', pdk_profile, name='pdk_profile'))
        urlpatterns.append(url(r'^unmatched-sources.json$', pdk_unmatched_sources, name='pdk_unmatched_sources'))
        urlpatterns.append(url(r'^logout$', logout, name='pdk_logout'))
        urlpatterns.append(url(r'^$', pdk_home, name='pdk_home'))
except AttributeError:
    pass


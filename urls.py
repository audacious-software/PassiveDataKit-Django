from django.conf.urls import url

from .views import add_data_point, add_data_bundle, pdk_home, unmatched_sources

urlpatterns = [
    url(r'^add-point.json$', add_data_point, name='pdk_add_data_point'),
    url(r'^add-bundle.json$', add_data_bundle, name='pdk_add_data_bundle'),
    url(r'^unmatched-sources.json$', unmatched_sources, name='pdk_unmatched_sources'),
    url(r'^$', pdk_home, name='pdk_home'),
]

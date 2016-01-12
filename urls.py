from django.conf.urls import url

from .views import add_data_point, add_data_bundle

urlpatterns = [
    url(r'^add-point.json$', add_data_point, name='add_data_point'),
    url(r'^add-bundle.json$', add_data_bundle, name='add_data_bundle'),
]

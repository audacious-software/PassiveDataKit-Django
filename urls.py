from django.conf.urls import url

from .views import add_data_point

urlpatterns = [
    url(r'^add.json$', add_data_point, name='add_data_point'),
]

from django.conf.urls.defaults import *
from django.conf import settings
from geonode.proxy.urls import urlpatterns as proxy_urlpatterns

from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('geonode.worldmap.hoods.views',
        (r'^$', 'create_hood'),
)
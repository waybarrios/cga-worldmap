from django.conf.urls import patterns, url, include
from django.conf import settings
from geonode.proxy.urls import urlpatterns as proxy_urlpatterns

urlpatterns = patterns('geonode.worldmap.hoods.views',
        (r'^$', 'create_hood'),
)

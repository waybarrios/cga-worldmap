from django.conf.urls.defaults import *
from django.conf import settings
from worldmap.sitemap import LayerSitemap, MapSitemap
from worldmap.proxy.urls import urlpatterns as proxy_urlpatterns

from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('worldmap.hoods.views',
        (r'^$', 'create_hood'),
)
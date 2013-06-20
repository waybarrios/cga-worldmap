from django.conf.urls.defaults import *

urlpatterns = patterns('geonode.worldmap.maputils.views',
    (r'^checkurl/?$', 'ajax_url_lookup'),
    url(r'^new/data$', 'new_map_json', name='new_map_json'),
    url(r'^(?P<mapid>\d+)/data$', 'map_json', name='map_json'),
    url(r'^(?P<mapid>\d+)/view$', 'map_view', name='map_view'),
    (r'', include('geonode.maps.urls')),
)
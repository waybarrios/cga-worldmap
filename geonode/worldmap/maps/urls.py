from django.conf.urls.defaults import *


urlpatterns = patterns('geonode.maps.views',
      url(r'^(?P<mapid>\d+)/data$', 'map_json', name='map_json'),
      url(r'^new/data$', 'new_map_json', name='new_map_json'),
)

urlpatterns += patterns('geonode.worldmap.maps.views',
    (r'^checkurl/?$', 'ajax_url_lookup'),
    (r'^history/(?P<mapid>\d+)/?$', 'ajax_snapshot_history'),
    url(r'^new$', 'new_map', name="new_map"),
    (r'^snapshot/create/?$', 'snapshot_create'),
    (r'^(?P<mapid>[^/]+)/(?P<snapshot>[A-Za-z0-9_\-]+)/?$', 'map_view'),
    (r'^(?P<mapid>[^/]+)/(?P<snapshot>[A-Za-z0-9_\-]+)/embed/?$', 'embed'),
    (r'^(?P<mapid>[^/]+)/(?P<snapshot>[A-Za-z0-9_\-]+)/mobile/?$', 'mobilemap'),   
    url(r'^(?P<mapid>[^/]+)/?$', 'map_view', name='map_view'),
    (r'', include('geonode.maps.urls')),
    (r'^(?P<mapid>[^/]+)/?$', 'map_view'),
)
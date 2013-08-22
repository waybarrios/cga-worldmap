from django.conf.urls.defaults import *
import geonode.maps.views


# urlpatterns = patterns('geonode.maps.views', 
#     url(r'^tag/(?P<slug>[-\w]+?)/$', 'maps_tag', name='maps_browse_tag'),
#     url(r'^embed/$', 'map_embed', name='map_embed'),
#     url(r'^(?P<layername>[^/]*)/attributes', 'maplayer_attributes', name='maplayer_attributes'),
#     url(r'^(?P<mapid>[^/]+)/info$', 'map_detail', name='map_detail'),
# )

urlpatterns = patterns('geonode.worldmap.maputils.views',
    (r'^checkurl/?$', 'ajax_url_lookup'),
    (r'^history/(?P<mapid>\d+)/?$', 'ajax_snapshot_history'),
    url(r'^(?P<mapid>\d+)/data$', 'map_json', name='map_json'),
    url(r'^new$', 'new_map', name="new_map"),
    url(r'^new/data$', 'new_map_json', name='new_map_json'),
    (r'^(?P<mapid>[^/]+)/(?P<snapshot>[A-Za-z0-9_\-]+)/?$', 'map_view'),
    (r'^(?P<mapid>[^/]+)/(?P<snapshot>[A-Za-z0-9_\-]+)/embed/?$', 'embed'),
    (r'^(?P<mapid>[^/]+)/(?P<snapshot>[A-Za-z0-9_\-]+)/mobile/?$', 'mobilemap'),   
    url(r'^(?P<mapid>[^/]+)/?$', 'map_view', name='map_view'),
    (r'', include('geonode.maps.urls')),
)
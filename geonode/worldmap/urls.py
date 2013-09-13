from django.conf.urls import include, patterns, url
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from geonode.sitemap import LayerSitemap, MapSitemap
import geonode.proxy.urls

import autocomplete_light
autocomplete_light.autodiscover()

urlpatterns = patterns('',
    ### WorldMap custom URL's
    url(r'^account/ajax_lookup_email$', 'geonode.worldmap.views.ajax_lookup_email',
                                       name='account_ajax_lookup_email'),
    (r"^account/", include("geonode.worldmap.register.urls")),
    (r'^people/', include('geonode.worldmap.profile.urls')),
    (r'^layers/', include('geonode.worldmap.layerutils.urls')),
    (r'^maps/', include('geonode.worldmap.maputils.urls')),
    #(r'^upload/', include('geonode.worldmap.uploadutils.urls')),
    (r'^annotations/', include('geonode.worldmap.mapnotes.urls')),
    url(r'^autocomplete/', include('autocomplete_light.urls')),
    url(r'^pin/registercomplete/$',
                           'geonode.worldmap.register.views.registercompleteOrganizationUser',
                           name='registration_complete'),
    (r'^bostonhoods/?', include('geonode.worldmap.hoods.urls')),
          
)
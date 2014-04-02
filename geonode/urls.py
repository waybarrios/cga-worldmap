from django.conf.urls import include, patterns, url
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.views.generic import TemplateView
from geonode.sitemap import LayerSitemap, MapSitemap
import geonode.proxy.urls
import geonode.maps.urls
import geonode.gazetteer.urls
import geonode.mapnotes.urls
import geonode.capabilities.urls


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
import autocomplete_light
autocomplete_light.autodiscover()
admin.autodiscover()

js_info_dict = {
    'domain': 'djangojs',
    'packages': ('geonode',)
}

sitemaps = {
    "layer": LayerSitemap,
    "map": MapSitemap
}

urlpatterns = patterns('',

    # Static pages
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='home'),
    url(r'^developer/$',  TemplateView.as_view(template_name='developer.html'), name='dev'),
    url(r'^upload_terms/$',  TemplateView.as_view(template_name='maps/upload_terms.html'), name='upload_terms'),

    # Services views
    (r'^services/', include('geonode.contrib.services.urls')),

     # Data views

     #For compatibility with newer version of geoserver-geonode-ext & GeoNode 2.0
     url(r'^layers/acls/?$', 'geonode.maps.views.layer_acls', name='data_acls'),
     url(r'^layers/resolve_user/?$', 'geonode.maps.views.resolve_user', name='layer_resolve_user'),

    (r'^data/', include(geonode.maps.urls.datapatterns)),
    (r'^maps/', include(geonode.maps.urls.urlpatterns)),
    (r'^annotations/', include(geonode.mapnotes.urls.urlpatterns)),
    (r'^comments/', include('dialogos.urls')),
    (r'^ratings/', include('agon_ratings.urls')),
    (r'^capabilities/', include('geonode.capabilities.urls')),
    # Accounts
    url(r'^accounts/ajax_login$', 'geonode.views.ajax_login',
        name='auth_ajax_login'),
    url(r'^accounts/ajax_lookup$', 'geonode.views.ajax_lookup',
        name='auth_ajax_lookup'),
    (r'^accounts/ajax_lookup_email$', 'geonode.views.ajax_lookup_email'),

    #(r'^accounts/login', 'django.contrib.auth.views.login'),
    #(r'^accounts/logout', 'django.contrib.auth.views.logout'),

    url(r"^account/", include("geonode.register.urls")),

    # Meta
    url(r'^lang\.js$', TemplateView.as_view(template_name='lang.js'), name='lang'),
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog',
        js_info_dict, name='jscat'),
    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap',
                                  {'sitemaps': sitemaps}, name='sitemap'),
    (r'^i18n/', include('django.conf.urls.i18n')),
    (r'^admin/', include(admin.site.urls)),
    (r'^affiliation/confirm', 'geonode.register.views.confirm'),
    (r'^avatar/', include('avatar.urls')),
    (r'^profiles/', include('geonode.profile.urls')),
    (r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
    (r'^download/(?P<service>[^/]*)/(?P<layer>[^/]*)/(?P<format>[^/]*)/?$','geonode.proxy.views.download'),
    (r'^gazetteer/', include('geonode.gazetteer.urls')),
    (r'^bostonhoods/?', include('geonode.hoods.urls')),
    (r'^certification/', include('geonode.certification.urls')),    
    url(r'^autocomplete/', include('autocomplete_light.urls')),
    (r'^search/?', include('geonode.search.urls')),
    )

urlpatterns += geonode.proxy.urls.urlpatterns


official_site_url_patterns = patterns('',
    (r'^tweetmap/$', 'geonode.maps.views.tweetview'),
    (r'^(?P<site>[A-Za-z0-9_\-]+)/$', 'geonode.maps.views.official_site'),
    (r'^(?P<site>[A-Za-z0-9_\-]+)/mobile/?$', 'geonode.maps.views.official_site_mobile'),
    (r'^(?P<site>[A-Za-z0-9_\-]+)/info$', 'geonode.maps.views.official_site_controller'),
)

urlpatterns += official_site_url_patterns

# Extra static file endpoint for development use
if settings.SERVE_MEDIA:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += patterns(
        url(r'^site_media/media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }))

# Serve static files
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

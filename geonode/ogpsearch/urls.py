
from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('geonode.ogpsearch.views',
    url(r'^geonode_to_solr$', 'geonode_to_solr'),
    url(r'^solr_to_geonode$', 'solr_to_geonode'),
    url(r'^$', 'index')

)

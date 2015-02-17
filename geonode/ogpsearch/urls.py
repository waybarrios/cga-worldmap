
from django.conf.urls.defaults import patterns, url

from . import views

urlpatterns = patterns('geonode.ogpsearch.views',
    url(r'^$', 'index'),
)
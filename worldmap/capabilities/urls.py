
from django.conf.urls.defaults import *

from worldmap.capabilities import views


urlpatterns = patterns('worldmap.capabilities.views',
    url(r'^map/(?P<mapid>\d+)/$', 'get_capabilities', name="capabilities_map"),
    url(r'^user/(?P<user>\w+)/$', 'get_capabilities', name="capabilities_user"),
    url(r'^category/(?P<category>\w+)/$', 'get_capabilities', name="capabilities_category"),
    )
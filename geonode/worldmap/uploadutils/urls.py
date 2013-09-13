from django.conf.urls.defaults import *
from geonode.upload.views import UploadFileCreateView

urlpatterns = patterns('geonode.upload.views',
    url(r'^new/$', UploadFileCreateView.as_view(), name='data_upload_new'),
    url(r'^progress$', 'data_upload_progress', name='data_upload_progress'),
)

urlpatterns += patterns('geonode.worldmap.uploadutils.views',
    url(r'^tab/?(?P<step>\w+)?$', 'view', name='data_upload'),
    url(r'^(?P<step>\w+)?$', 'view', name='data_upload'),
    (r'', include('geonode.upload.urls'))
)

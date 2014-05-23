from django.conf.urls.defaults import *
import account.views
from geonode.worldmap.register.views import SignupView, registercompleteOrganizationUser, forgot_username


urlpatterns = patterns('',
                       url(r"^signup/$", SignupView.as_view(), name="account_signup"),
                       url(r'^forgotname',forgot_username,name='forgot_username'),
                       url(r'^registercomplete/$',
                           registercompleteOrganizationUser,
                           name='registration_complete'),
                       (r'', include('account.urls')),
                       )

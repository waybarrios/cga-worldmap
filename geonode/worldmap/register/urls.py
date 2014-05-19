from django.conf.urls import patterns, url, include
from geonode.worldmap.register.views import SignupView, registercompleteOrganizationUser, forgotUsername
from geonode.worldmap.register.forms import UserRegistrationForm

urlpatterns = patterns('',
                       url(r"^signup/$", SignupView.as_view(), name="account_signup"),
                       url(r'^forgotname/$',
                           forgotUsername, name="account_forgotname"),
                       url(r'^registercomplete/$',
                           registercompleteOrganizationUser,
                           name='registration_complete'),
                       (r'', include('account.urls')),
                       )


from django.conf.urls.defaults import *
from geonode.account.views import SignupView, registercompleteOrganizationUser, forgotUsername
from geonode.account.forms import UserRegistrationForm

urlpatterns = patterns('',
                       url(r"^signup/$", SignupView.as_view(), name="account_signup"),
                       url(r'^forgotname/$',
                           forgotUsername, name="account_forgotname"),
                       (r'', include('account.urls')),
                       )


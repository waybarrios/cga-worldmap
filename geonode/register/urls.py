from django.conf.urls.defaults import *
import account.views
from geonode.register.views import SignupView, registercompleteOrganizationUser
from geonode.register.forms import UserRegistrationForm

urlpatterns = patterns('',
                       url(r"^account/signup/$", SignupView.as_view(), name="account_signup"),
                       url(r'^registercomplete/$',
                           registercompleteOrganizationUser,
                           name='registration_complete'),
                       (r'', include('account.urls')),
                       )

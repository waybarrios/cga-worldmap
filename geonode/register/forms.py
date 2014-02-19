# -*- coding: UTF-8 -*-
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
import account
from django.utils.translation import ugettext_lazy as _
from geonode.maps.models import Contact


attrs_dict = { 'class': 'required' }

class ForgotUsernameForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
        maxlength=75)),
        label=_(u'Email Address'))


class UserRegistrationForm(account.forms.SignupForm):
    if (settings.USE_CUSTOM_ORG_AUTHORIZATION):
        is_org_member = forms.TypedChoiceField(coerce=lambda x: bool(int(x)),
                                               choices=((1, _(u'Yes')), (0, _(u'No'))),
                                               widget=forms.RadioSelect,
                                               initial=0, label=settings.CUSTOM_ORG_AUTH_TEXT
        )

# -*- coding: UTF-8 -*-
from django.forms import ModelForm
from geonode.people.models import Profile


attrs_dict = { 'class': 'required' }

class ContactProfileForm(ModelForm):
    class Meta:
        model = Profile
        exclude = ('is_org_member', 'user', 'member_expiration_dt', 'is_certifier')
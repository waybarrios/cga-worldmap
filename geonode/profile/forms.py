# -*- coding: UTF-8 -*-
from django.forms import ModelForm
from geonode.profile.models import WorldmapProfile


attrs_dict = { 'class': 'required' }

class ContactProfileForm(ModelForm):
    class Meta:
        model = WorldmapProfile
        exclude = ('is_org_member', 'user', 'member_expiration_dt')
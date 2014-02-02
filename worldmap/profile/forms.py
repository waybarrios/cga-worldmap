# -*- coding: UTF-8 -*-
from django.forms import ModelForm
from worldmap.maps.models import Contact


attrs_dict = { 'class': 'required' }

class ContactProfileForm(ModelForm):
    class Meta:
        model = Contact
        exclude = ('is_org_member', 'user', 'member_expiration_dt', 'is_certifier')
# -*- coding: UTF-8 -*-
from django import forms
from django.utils.translation import ugettext as _
from geonode.people.models import Profile
import autocomplete_light

attrs_dict = { 'class': 'required' }

class ContactProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ('is_org_member', 'user', 'member_expiration_dt')
        
class LayerContactForm(forms.Form):
    poc = forms.ModelChoiceField(empty_label = _("Person outside WorldMap (fill form)"),
        label = "*" + _("Point Of Contact"), required=False,
        queryset = Profile.objects.exclude(user=None),
        widget=autocomplete_light.ChoiceWidget('ProfileAutocomplete'))

    metadata_author = forms.ModelChoiceField(empty_label = _("Person outside WorldMap (fill form)"),
        label = _("Metadata Author"), required=False,
        queryset = Profile.objects.exclude(user=None),
        widget=autocomplete_light.ChoiceWidget('ProfileAutocomplete'))
    
    class Meta:
        model = Profile
        
        
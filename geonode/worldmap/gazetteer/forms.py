from django import forms
from django.utils.translation import ugettext as _
from geonode.layers.models import Attribute

class GazetteerForm(forms.Form):
    project = forms.CharField(label=_('Project'), max_length=128, required=False)
    startDate = forms.ModelChoiceField(label = _("Start Date attribute"),
                                       required=False,
                                       queryset = Attribute.objects.none())

    startDateFormat = forms.CharField(label=_("Date format"), max_length=256, required=False)

    endDate = forms.ModelChoiceField(label = _("End Date attribute"),
                                     required=False,
                                     queryset = Attribute.objects.none())

    endDateFormat = forms.CharField(label=_("Date format"), max_length=256, required=False)
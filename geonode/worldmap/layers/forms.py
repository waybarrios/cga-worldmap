
# -*- coding: utf-8 -*-
from django import forms
from django.utils import simplejson as json
from geonode.upload.forms import LayerUploadForm
from geonode.layers.models import Layer, Attribute
from geonode.base.models import TopicCategory
import taggit
from django.utils.translation import ugettext as _
from re import escape

GEOMETRY_CHOICES = [
    ['Point', 'Points'],
    ['LineString', 'Lines'],
    ['Polygon', 'Polygons (Shapes)']
]


TYPE_CHOICES = (
       ('java.lang.Boolean', 'Boolean (true/false)'),
       ('java.util.Date', 'Date/Time'),
       ('java.lang.Float', 'Number (Float)'),
       ('java.lang.Integer', 'Number (Integer)'),
       ('java.lang.String', 'Text'),
)

CONSTRAINT_OPTIONS = [
    # These should match database entries for base.restrictioncodetype
    ['Public Domain Dedication and License (PDDL)',_('Public Domain Dedication and License (PDDL)')],
    ['Attribution License (ODC-By)', _('Attribution License (ODC-By)')],
    ['Open Database License (ODC-ODbL)',_('Open Database License (ODC-ODbL)')],
    ['CC-BY-SA',_('CC-BY-SA')],

    # ISO standard constraint options.
    ['copyright', _('Copyright')],
    ['patent', _('Patent')],
    ['patentPending', _('Patent Pending')],
    ['trademark', _('Trademark')]
]


class LayerCategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return '<a href="#" onmouseover=\'javascript:showModal("' + escape(obj.description) + '")\' onmouseout=\'javascript:hideModal()\';return false;\'>' + obj.gn_description + '</a>'



class LayerCategoryForm(forms.Form):
    category_choice_field = LayerCategoryChoiceField(required=False, label = '*' + _('Category'), empty_label=None,
        queryset = TopicCategory.objects.extra(order_by = ['description']))


    def clean(self):
        cleaned_data = self.data
        ccf_data = cleaned_data.get("category_choice_field")


        if not ccf_data:
            msg = u"This field is required."
            self._errors = self.error_class([msg])

        # Always return the full collection of cleaned data.
        return cleaned_data

class JSONField(forms.CharField):
    def clean(self, text):
        text = super(JSONField, self).clean(text)
        try:
            return json.loads(text)
        except ValueError:
            raise forms.ValidationError("this field must be valid JSON")

class LayerCreateForm(forms.Form):
    name = forms.CharField(label="Name", max_length=256,required=True)
    title = forms.CharField(label="Title",max_length=256,required=True)
    srs = forms.CharField(label="Projection",initial="EPSG:4326",required=True)
    geom = forms.ChoiceField(label="Data type", choices=GEOMETRY_CHOICES,required=True)
    keywords = forms.CharField(label = '*' + ('Keywords (separate with spaces)'), widget=forms.Textarea)
    abstract = forms.CharField(widget=forms.Textarea, label="Abstract", required=True)
    permissions = JSONField()

class WorldMapLayerUploadForm(LayerUploadForm):
    abstract = forms.CharField(required=True, error_messages={'required': 'Abstract is required'})
    layer_title = forms.CharField(required=True, error_messages={'required': 'Title is required'})
    keywords = forms.CharField(required=True, error_messages={'required': 'Keywords required'})
    
class WorldMapLayerForm(forms.ModelForm):
    CONSTRAINT_HELP = _('''<p>Please choose the appropriate type of restriction (if any) for the use of your data. 
    Then use the "Restrictions Other" form below to provide any necessary details.</p>
    ''')
    
    map_id = forms.CharField(widget=forms.HiddenInput(), initial='', required=False)
    date = forms.DateTimeField(label='*' + (_('Date')), widget=forms.SplitDateTimeWidget)
    date.widget.widgets[0].attrs = {"class":"datepicker", 'data-date-format': "yyyy-mm-dd"}
    date.widget.widgets[1].attrs = {"class":"time"}
    temporal_extent_start = forms.DateField(label= _('Temporal Extent Start Date'),required=False,widget=forms.DateInput(attrs={"class":"datepicker", 'data-date-format': "yyyy-mm-dd"}))
    temporal_extent_end = forms.DateField(label= _('Temporal Extent End Date'),required=False,widget=forms.DateInput(attrs={"class":"datepicker", 'data-date-format': "yyyy-mm-dd"}))
    title = forms.CharField(label = '*' + _('Title'), max_length=255)
    abstract = forms.CharField(label = '*' + _('Abstract'), widget=forms.Textarea(attrs={'cols': 60}))

    keywords = taggit.forms.TagField(required=False,
                                     help_text=_("A space or comma-separated list of keywords"))
    class Meta:
        model = Layer
        exclude = ('contacts','workspace', 'store', 'name', 'uuid', 'storeType', 'typename',
                   'bbox_x0', 'bbox_x1', 'bbox_y0', 'bbox_y1', 'srid','topic_category', 'category',
                   'csw_typename', 'csw_schema', 'csw_mdsource', 'csw_type',
                   'csw_wkt_geometry', 'metadata_uploaded', 'metadata_xml', 'csw_anytext',
                   'popular_count', 'share_count', 'thumbnail', 'default_style', 'styles',
                    'gazetteer_project', 'in_gazetteer')
        
        
class GazetteerAttributeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(GazetteerAttributeForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.attribute_type != 'xsd:string':
            self.fields['searchable'].widget.attrs['disabled'] = True
        self.fields['attribute'].widget.attrs['readonly'] = True
        self.fields['display_order'].widget.attrs['size'] = 3
        self.fields['display_order'].widget.attrs['style'] = "width:50px;"

    class Meta:
        model = Attribute
        exclude = ('attribute_type','count','min','max','average','median','stddev',
                   'sum','unique_values','last_stats_updated','objects')
    

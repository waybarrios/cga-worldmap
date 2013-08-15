from django.db import models
from django.db.models import signals
from geonode.layers.models import Attribute, Layer
from django.utils.translation import ugettext_lazy as _

# Create your models here.
class SearchAttribute(Attribute):
    #attribute = models.ForeignKey(Attribute, blank=False, null=False, unique=True)
    #layer = models.ForeignKey(Layer, blank=False, null=False, unique=True)
    searchable = models.BooleanField(_('Searchable?'), default=False)
    in_gazetteer = models.BooleanField(_('In Gazetteer?'), default=False)
    is_gaz_start_date = models.BooleanField(_('Gazetteer Start Date'), default=False)
    is_gaz_end_date = models.BooleanField(_('Gazetteer End Date'), default=False)
    date_format = models.CharField(_('Date Format'), max_length=255, blank=True, null=True)
    
    
def create_layer_attribute(instance, sender, **kwargs):
    try:
        SearchAttribute.objects.get(attribute_ptr_id=instance.pk)
    except:
        la = SearchAttribute(attribute_ptr_id=instance.pk)
        la.__dict__.update(instance.__dict__)
        la.searchable = True if instance.attribute_type == 'xsd-string' else False
        la.save()
    
signals.post_save.connect(create_layer_attribute, sender=Attribute)
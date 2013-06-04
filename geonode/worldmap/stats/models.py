from django.db import models
from geonode.maps.models import Map
from geonode.layers.models import Layer
from django.utils.translation import ugettext_lazy as _

# Create your models here.
#===================#
#    NEW WORLDMAP MODELS      #
#===================#

class MapStats(models.Model):
    map = models.ForeignKey(Map, unique=True)
    visits = models.IntegerField(_("Visits"), default= 0)
    uniques = models.IntegerField(_("Unique Visitors"), default = 0)
    last_modified = models.DateTimeField(auto_now=True,null=True)

class LayerStats(models.Model):
    layer = models.ForeignKey(Layer, unique=True)
    visits = models.IntegerField(_("Visits"), default = 0)
    uniques = models.IntegerField(_("Unique Visitors"), default = 0)
    downloads = models.IntegerField(_("Downloads"), default = 0)
    last_modified = models.DateTimeField(auto_now=True, null=True)
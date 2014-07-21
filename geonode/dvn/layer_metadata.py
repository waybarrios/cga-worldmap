if __name__=='__main__':
    import os, sys
    DJANGO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(DJANGO_ROOT)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings.local'

import logging

from django.conf import settings

from geonode.maps.models import Layer
from geonode.dvn.dv_utils import remove_whitespace_from_xml, MessageHelperJSON

logger = logging.getLogger("geonode.dvn.layer_metadata")


class LayerMetadata:
    """Object used to format JSON and send information back to DVN"""
    
    METADATA_ATTRIBUTES = ['layer_name', 'layer_link', 'embed_map_link', 'worldmap_username']
    
    def __init__(self, **kwargs):
        # Initialize attributes
        
        # Initialize attributes or set them directly from kwargs
        for attr in self.METADATA_ATTRIBUTES:
            self.__dict__[attr] = kwargs.get(attr, None)

        # Is an entire name being passed?
        geonode_layer_name = kwargs.get('geonode_layer_name', None)
        if geonode_layer_name:
            self.update_metadata_with_layer_name(geonode_layer_name)

        # Is the entire layer being passed?
        geonode_layer_object = kwargs.get('geonode_layer_object', None)
        if geonode_layer_object:
            self.update_metadata_with_layer_object(geonode_layer_object)


    def get_metadata_dict(self, as_json=False):
        
        json_dict = {}
        for attr in self.METADATA_ATTRIBUTES:
            json_dict[attr] = self.__dict__.get(attr, None)
        
        if as_json:
            try:
                return json.dumps(json_dict)
            except:
                logger.warn('Failed to convert metadata to JSON')
                return None
                                
        return json_dict


    def update_metadata_with_layer_name(self, layer_name):
        if not layer_name:
            return False

        try:
            layer_obj = Layer.objects.get(name=layer_name)
        except Layer.DoesNotExist:
            return False
            
        return self.update_metadata_with_layer_object(layer_obj)
        
    def update_metadata_with_layer_object(self, layer_obj):
        if not type(layer_obj) is Layer:
            return False

        self.layer_name = layer_obj.typename
        self.layer_link = '%sdata/%s' % (settings.SITEURL, layer_obj.service_typename)
        self.embed_map_link =  '%smaps/embed/?layer=%s' % (settings.SITEURL, layer_obj.service_typename)
        if layer_obj.owner:
            self.worldmap_username =  layer_obj.owner.username
            
        return True


if __name__=='__main__':
    layer = None
    try:
        layer = Layer.objects.get(name='boston_income_2_8p6')
    except Layer.DoesNotExist:
        print 'layer does not exist'
    if layer:
        print type(layer)
        print dir(layer)
        print layer.owner.username
        lm = LayerMetadata(**{'geonode_layer_object':layer})
        print lm.get_metadata_dict()
if __name__=='__main__':
    import os, sys
    DJANGO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(DJANGO_ROOT)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings.local'

import logging
import os
from random import choice
import re
from xml.etree.ElementTree import XML, ParseError

from django.utils.translation import ugettext as _
from django.conf import settings

from geonode.maps.models import Layer


logger = logging.getLogger("geonode.dvn.sld_test")


def add_sld(layer_name):

    sld_xml_content = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_rules', 'test_rules_03.xml'), 'r').read()


    #   (1) Make a preliminary check of the SLD XML
    #
    print ('(1) Make a preliminary check of the SLD XML')
    try:
        sldxml = XML(sld_xml_content)
        valid_url = re.compile(settings.VALID_SLD_LINKS)
        for elem in sldxml.iter(tag='{http://www.opengis.net/sld}OnlineResource'):
            if '{http://www.w3.org/1999/xlink}href' in elem.attrib:
                link = elem.attrib['{http://www.w3.org/1999/xlink}href']
                if valid_url.match(link) is None:
                    raise Exception(_("External images in your SLD file are not permitted.  Please contact us if you would like your SLD images hosted on %s") % (settings.SITENAME))
    except ParseError, e:
        msg =_('Your SLD file contains invalid XML')
        logger.warn("%s - %s" % (msg, str(e)))
        e.args = (msg,)
        return
    print 'ok so far'


    #  (2) Get the catalog 
    print ('(2) Get the catalog ')
    
    gs_catalog_obj = Layer.objects.gs_catalog

    #   (3) Retrieve the layer for the new style
    #    
    print ('(3) Retrieve the layer for the new style')
    layer_obj = gs_catalog_obj.get_layer(layer_name)
    if layer_obj is None:
         msg = _('The layer "%s" does not exist' % layer_name)
         logger.warn("%s - %s" % (msg, str(e)))
         print msg
         return
    print 'layer_obj', layer_obj
    """
    try:
        layer_obj = Layer.objects.get(name=layer_name)
    except Layer.DoesNotExist:
       
    """

    #return
        
    #  (4) Create the style
    if 1: #try:
        stylename = layer_name + "_".join([choice('qwertyuiopasdfghjklzxcvbnm0123456789') for i in range(4)])
        print ('style name: %s' %stylename)
        gs_catalog_obj.create_style(stylename, sld_xml_content)
        
        print 'style created'
        # set the style as the default
        layer_obj.default_style = gs_catalog_obj.get_style(stylename)
        print dir(layer_obj)
        gs_catalog_obj.save(layer_obj)

    #except geoserver.catalog.ConflictingDataError, e:
    #    msg = (_('There is already a style in GeoServer named ') +
    #       '"%s"' % (name))
    #    logger.warn(msg)
    #    e.args = (msg,)
        
if __name__=='__main__':
    add_sld('income_2so')


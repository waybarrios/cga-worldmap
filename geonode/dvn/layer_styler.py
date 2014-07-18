from __future__ import print_function

import json
import logging
import sys

from django.conf import settings

from geonode.dvn.sld_helper_form import SLDHelperForm
from geonode.dvn.sld_maker import StyleLayerMaker
from geonode.dvn.sld_rule_formatter import SLDRuleFormatter
from geonode.dvn.geonode_get_services import get_sld_rules

logger = logging.getLogger("geonode.dvn.layer_styler")

class LayerStyler:
    def __init__(self, styling_params):
        self.styling_params = styling_params
        self.layer_name = None
        self.err_found = False
        self.err_msgs = []
    
    
    def get_json_as_dict(self, resp_json, default_msg):
        try:
            return json.loads(resp_json)
        except:
            return {'success' : False, 'message' : default_msg}
    
    def style_layer(self):
        
        # (1) Check params and create rules
        #
        sld_rule_data = self.set_layer_name_and_get_rule_data()
        if sld_rule_data is None:
            return False
        
        # (2) Format rules into full SLD
        #
        formatted_sld = self.format_rules_into_full_sld(sld_rule_data)
        if formatted_sld is None:
            return False
        
        # (3) Add new SLD to Layer
        #
        return self.add_new_sld_to_layer(formatted_sld)
    
    
    def add_new_sld_to_layer(self, formatted_sld):
        """ 
        (3) Add new SLD to Layer
        """
        if not formatted_sld:
            self.add_err_msg('Formatted SLD data is not available')
            return False
        
        slm = StyleLayerMaker(layer_name)
        succcess = slm.add_sld_xml_to_layer(formatted_sld)
        if succcess:
            return True
    
        for err in slm.err_msgs:
            self.add_err_msg(err)
        
        return False
        
        
    def format_rules_into_full_sld(self, sld_rule_data):
        """ 
        (2) Format rules into full SLD
        """
        if not sld_rule_data:
            self.add_err_msg('Rule data is not available')
            return None

        if not self.layer_name:
            self.add_err_msg('Layer name is not available')
            return None
            
        sld_formatter = SLDRuleFormatter(self.layer_name)
        
        formatted_sld = sld_formatter.get_sld_xml(sld_rule_data)

        if formatted_sld is None:
            self.add_err_msg('Failed to format xml')
            if sld_formatter.err_found:
                self.add_err_msg('\n'.join(sld_formatter.err_msgs))
            return None
            
        return formatted_sld
        
    
    def set_layer_name_and_get_rule_data(self):
        """
        (1) Check params and create rules
        """
        if self.styling_params is None:
            return None
        
        resp_json = get_sld_rules(self.styling_params)
        
        resp_dict = self.get_json_as_dict(resp_json, 'Failed to make the SLD rules')
        
        if not resp_dict.get('success') is True:
            msg = resp_dict.get('message',)
            self.add_err_msg(msg)
            for err_msg in resp_dict.get('data', []):
                self.add_err_msg(err_msg)
            return None

        # (1a) Pull layer name from initial params, should never fail b/c params have been evaluated in (1)
        #
        self.layer_name = self.styling_params.get('layer_name', None)
        if self.layer_name is None:
            self.add_err_msg('Layer name is not in the parameters')
            return None

        sld_rule_data = resp_dict.get('data', {}).get('style_rules', None)
        if sld_rule_data is None:
            self.add_err_msg('Failed to find rules in response')
            return None
        
        return sld_rule_data
        
        
    def get_json_message(self):
        if not self.err_found:
            """
            
            return HttpResponse(status=200, content=json.dumps({
                "success": True,
                "layer_name": saved_layer.typename,
                "layer_link": "%sdata/%s" % (settings.SITEURL, saved_layer.service_typename),
                "embed_map_link": "%smaps/embed/?layer=%s" % (settings.SITEURL, saved_layer.service_typename),
                "worldmap_username": user.username
            })
            """
            pass
        pass
        
  
    def add_err_msg(self, msg):
        self.err_found = True
        self.err_msgs.append(msg)
        logger.warn(msg)


if __name__=='__main__':
    layer_name = 'boston_census_r5j'
    
    d = dict(layer_name=layer_name\
                , attribute='TWORACES'\
                ,method='jenks'\
                ,intervals=5\
                ,ramp='Blue'\
                ,startColor='#fff5f0'\
                ,endColor='#67000d'\
                ,reverse=''\
            )
    ls = LayerStyler(d)
    worked = ls.style_layer()
    if not worked:
        print ('\n'.join(ls.err_msgs))
    else:
        print ('Yes!')
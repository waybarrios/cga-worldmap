
if __name__=='__main__':
    import os, sys
    DJANGO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(DJANGO_ROOT)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings.local'

import logging
import random
import string

from geonode.dvn.dv_utils import remove_whitespace_from_xml, MessageHelperJSON
from lxml import etree

logger = logging.getLogger("geonode.dvn.sld_rule_formatter")

"""
Class to help create an SLD with Rules
"""
class SLDRuleFormatter:
    
    RULES_START_TAG = '<Rules>'
    RULES_END_TAG = '</Rules>'
    
    def __init__(self, layer_name, sld_name=None):
        self.layer_name = layer_name
        self.sld_name = sld_name
        self.err_found = False
        self.err_msgs = []
        
        if self.sld_name is None:
            self.sld_name = self.generate_sld_name()

    def add_err_msg(self, msg):
        self.err_found = True
        self.err_msgs.append(msg)
        logger.warn(msg)
        
    def id_generator(self, size=7, chars=string.ascii_lowercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))
        
    def generate_sld_name(self):

        random_id =  self.id_generator()
        return '%s_%s' % (self.layer_name, random_id)
        

    def format_rules_xml(self, rules_xml):
        """
        Given a XML in <Rules>...</Rules> tags, remove the outer tags
        
        <Rules>
            <Rule>....</Rule>
        </Rules>
        """
        if not rules_xml:
            return None
        
        # Formerly parsed XML tree, etc, but this seemed a bit easier
        return rules_xml.replace(self.RULES_START_TAG, '').replace(self.RULES_END_TAG, '')
        
        
        
    def get_sld_xml(self, rules_xml):
        if not rules_xml:
            return None
            
        rules_xml_formatted = self.format_rules_xml(rules_xml)
        if rules_xml_formatted is None:
            return None
        #print 'rules_xml_formatted', rules_xml_formatted

        xml_str = """<?xml version="1.0"?>
        <sld:StyledLayerDescriptor xmlns:sld="http://www.opengis.net/sld" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:ogc="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" version="1.0.0" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
            <sld:NamedLayer>
                <sld:Name>geonode:%s</sld:Name>
                <sld:UserStyle>
                    <sld:Name>%s</sld:Name>
                    <sld:FeatureTypeStyle>%s</sld:FeatureTypeStyle>
                </sld:UserStyle>
            </sld:NamedLayer>
        </sld:StyledLayerDescriptor>""" % (self.layer_name, self.sld_name, rules_xml_formatted)
        

        xml_str = remove_whitespace_from_xml(xml_str)
        if xml_str is None:
            return None
            
        return xml_str

    def get_test_rules(self):
        
        return """<Rules>
          <Rule>
            <Title> &gt; -2.7786 AND &lt;= 2.4966</Title>
            <Filter>
              <And>
                <PropertyIsGreaterThanOrEqualTo>
                  <PropertyName>Violence_4</PropertyName>
                  <Literal>-2.7786</Literal>
                </PropertyIsGreaterThanOrEqualTo>
                <PropertyIsLessThanOrEqualTo>
                  <PropertyName>Violence_4</PropertyName>
                  <Literal>2.4966</Literal>
                </PropertyIsLessThanOrEqualTo>
              </And>
            </Filter>
            <PolygonSymbolizer>
              <Fill>
                <CssParameter name="fill">#424242</CssParameter>
              </Fill>
              <Stroke/>
            </PolygonSymbolizer>
          </Rule>
          <Rule>
            <Title> &gt; 13.047 AND &lt;= 18.3222</Title>
            <Filter>
              <And>
                <PropertyIsGreaterThan>
                  <PropertyName>Violence_4</PropertyName>
                  <Literal>13.047</Literal>
                </PropertyIsGreaterThan>
                <PropertyIsLessThanOrEqualTo>
                  <PropertyName>Violence_4</PropertyName>
                  <Literal>18.3222</Literal>
                </PropertyIsLessThanOrEqualTo>
              </And>
            </Filter>
            <PolygonSymbolizer>
              <Fill>
                <CssParameter name="fill">#B0B0B0</CssParameter>
              </Fill>
              <Stroke/>
            </PolygonSymbolizer>
          </Rule>
        </Rules>"""

if __name__=='__main__':
    sld_formatter = SLDRuleFormatter('layer-name')
    print sld_formatter.get_sld_xml(sld_formatter.get_test_rules())
       
if __name__=='__main__':
    import os, sys
    DJANGO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(DJANGO_ROOT)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings.local'


import httplib2
try:
    from urlparse import urljoin
except:
    from urllib.parse import urljoin        # python 3.x
import xmltodict


from django.conf import settings
from geonode.maps.models import Layer
from geonode.dvn.dv_utils import remove_whitespace_from_xml, MessageHelperJSON
from geonode.dvn.forms import SLDHelperForm
from geonode.dvn.sld_helper import SLDRuleHelper
from geonode.dvn.dv_utils import remove_whitespace_from_xml
METHOD_POST = 'POST'
METHOD_PUT = 'PUT'
ACCEPTED_METHODS = (METHOD_POST, METHOD_PUT)

def make_geoserver_post_put_request(request_url_str, method_type=METHOD_POST,  **kwargs):
    """
    Convenience function used to make GET requests to the geoserver
    
    Optional kwargs:
    
    :param content_type: str, type of requests, e.g. "application/xml", "application/json"
    :param request_data: str, e.g. XML or JSON data in string format
    
    """
    if not request_url_str:
        return (None, None)

    if not method_type in ACCEPTED_METHODS:
        # log.illegal method
        print ('Method must be in %s' % ACCEPTED_METHODS)
        return (None, None)

    headers = dict()
    content_type = kwargs.get('content_type', None)
    if content_type is not None:
        headers["Content-Type"] = content_type
        
    request_data = kwargs.get('request_data', None)

    # Prepare geo server request
    http = httplib2.Http()
    http.add_credentials(*settings.GEOSERVER_CREDENTIALS)

    print '\nrequest_url_str', request_url_str
    print '\nrequest_data', request_data
    print '\nheaders', headers
    response, content = http.request(request_url_str\
                          , method_type\
                          , body=request_data\
                          , headers=headers\
                          )
    return (response, content)

def test_add_new_style(layer_name='income_2so'):

    create_new_style(layer_name)


def associate_new_style_with_layer(layer_name, style_name):
    
    json_data = """{"layer":{"defaultStyle":{"name":"%s"},"styles":{},"enabled":true}}""" % (style_name)
    
    url_str = 'rest/layers/geonode:%s.json' % (layer_name)
    associate_sld_url = urljoin(settings.GEOSERVER_BASE_URL, url_str)
    
    params = { 'content_type' : 'application/json; charset=UTF-8'\
               , 'request_data' : json_data\
               }
    
    (response, content) = make_geoserver_post_put_request(associate_sld_url, METHOD_PUT, **params)
    
    print 'response', response
    
    print 'content', content

    
    
def create_new_style(layer_name, sld_xml=None):
    
    sld_helper = SLDRuleHelper(layer_name)
    
    # Test 1: Add new rules to SLD template
    #test_rules_fname = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_rules', 'test_rules_01.xml')
    #test_rules_xml = open(test_rules_fname, 'r').read()
    #xml_data = sld_helper.get_sld_xml(test_rules_xml)

    # Test 2: Straight read from a new file
    # straight read from known file to test if post request works
    xml_data = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_rules', 'test_rules_02.xml'), 'r').read()
    
    print 'xml_data', xml_data

    xml_data = remove_whitespace_from_xml(xml_data)
    print 'xml_data', xml_data
    url_str = 'rest/styles/%s.xml' % layer_name
    make_new_sld_url = urljoin(settings.GEOSERVER_BASE_URL, url_str)
    
    print ('make_new_sld_url', make_new_sld_url)
    #application/vnd.ogc.sld+xml; charset=UTF-8
    params = { 'content_type' : 'application/vnd.ogc.sld+xml; charset=UTF-8'    #'application/xml'\
                , 'request_data' : xml_data\
            }
    (response, content) = make_geoserver_post_put_request(make_new_sld_url, METHOD_PUT, **params)

    print 'response', response
    
    print 'content', content
    
    print 'new style name', sld_helper.sld_name
    

if __name__=='__main__':
    create_new_style('income_2so')
    associate_new_style_with_layer('income_2so', 'income_2so_388wd0c')

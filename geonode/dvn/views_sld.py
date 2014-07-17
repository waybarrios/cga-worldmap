import json
import urllib

from django.http import HttpResponse
from django.conf import settings
from dv_utils import MessageHelperJSON
from dataverse_auth import has_proper_auth
from geonode.dvn.geonode_get_services import get_layer_features_definition
from geonode.dvn.sld_helper_form import SLDHelperForm

#from proxy.views import geoserver_rest_proxy

# http://localhost:8000/gs/rest/sldservice/geonode:boston_social_disorder_pbl/classify.xml?attribute=Violence_4&method=equalInterval&intervals=5&ramp=Gray&startColor=%23FEE5D9&endColor=%23A50F15&reverse=

def view_layer_feature_defn(request, layer_name):
    """
    Given a layer name, retrieve a desciption of the field names in values.
    This will be in XML format.
    
    example: http://localhost:8000/dvn/describe-features/income_4x5/
    """    
    #if not has_proper_auth(request):
    #    json_msg = MessageHelperJSON.get_json_msg(success=False, msg="Not permitted")    
    #    return HttpResponse(content=json_msg, content_type="application/json")
        
    json_msg = get_layer_features_definition(layer_name)
    return HttpResponse(content=json_msg, content_type="application/json")


def get_sld_rules(request, params):
    #http://localhost:8000/gs/rest/layers/geonode:boston_social_disorder_pbl.json
    params = dict(layer_name='boston_social_disorder_pbl'\
                , attribute='Violence_4'\
                ,method='equalInterval'\
                ,intervals=5\
                ,ramp='Gray'\
                ,startColor='#FEE5D9'\
                ,endColor='#A50F15'\
                ,reverse=''\
            )
            
    f = SLDHelperForm(d)
    if f.is_valid():
        print 'valid'
        print f.cleaned_data
        print f.get_url_params_str()
    else:
        #print f.errors.items()
        for err_tuple in f.errors.items():
            field_name, err_list = err_tuple
            for err in err_list:
                print field_name, err





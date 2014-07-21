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

import logging

from django.conf import settings


logger = logging.getLogger("geonode.dvn.geonode_post_services")


def make_geoserver_json_put_request(request_url_str, json_data_str):

    content_type = 'application/json; charset=UTF-8'
    return make_geoserver_put_request(request_url_str, json_data_str, content_type)

def make_geo_server_put_sld_request(request_url_str, xml_data):

    content_type = 'application/vnd.ogc.sld+xml; charset=UTF-8'
    return make_geoserver_put_request(request_url_str, xml_data, content_type)
    

def make_geoserver_put_request(request_url_str, data, content_type):
    """
    Convenience function used to make GET requests to the geoserver
    """
    if not request_url_str:
        return (None, None)

    # Prepare geo server request
    http = httplib2.Http()
    http.add_credentials(*settings.GEOSERVER_CREDENTIALS)
    headers = dict()
    headers["Content-Type"] = content_type

    response, content = http.request(request_url_str\
                                     , 'PUT'\
                                     , body=data\
                                     , headers=headers\
                                     )
    return (response, content)


# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.http import HttpResponse
from httplib import HTTPConnection, HTTPSConnection
from urlparse import urlsplit
import httplib2
import urllib
from django.utils import simplejson as json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
import logging
from urlparse import urlparse
from geonode.layers.models import Layer
from geonode.worldmap.stats.models import LayerStats
import re
import random
from geonode.utils import ogc_server_settings


logger = logging.getLogger("geonode.proxy.views")

HGL_URL = 'http://hgl.harvard.edu:8080/HGL'

@csrf_exempt
def proxy(request):
    if 'url' not in request.GET:
        return HttpResponse(
                "The proxy service requires a URL-encoded URL as a parameter.",
                status=400,
                content_type="text/plain"
                )

    url = urlsplit(request.GET['url'])
    locator = url.path
    if url.query != "":
        locator += '?' + url.query
    if url.fragment != "":
        locator += '#' + url.fragment

    headers = {}
    if settings.SESSION_COOKIE_NAME in request.COOKIES:
        headers["Cookie"] = request.META["HTTP_COOKIE"]

    if request.method in ("POST", "PUT") and "CONTENT_TYPE" in request.META:
        headers["Content-Type"] = request.META["CONTENT_TYPE"]

    conn = HTTPConnection(url.hostname, url.port) if url.scheme == "http" else HTTPSConnection(url.hostname, url.port)
    conn.request(request.method, locator, request.raw_post_data, headers)
    result = conn.getresponse()
    response = HttpResponse(
            result.read(),
            status=result.status,
            content_type=result.getheader("Content-Type", "text/plain")
            )
    return response

@csrf_exempt
def geoserver_rest_proxy(request, proxy_path, downstream_path):
    if not request.user.is_authenticated():
        return HttpResponse(
            "You must be logged in to access GeoServer",
            mimetype="text/plain",
            status=401)

    def strip_prefix(path, prefix):
        assert path.startswith(prefix)
        return path[len(prefix):]

    path = strip_prefix(request.get_full_path(), proxy_path)
    url = "".join([ogc_server_settings.LOCATION, downstream_path, path])

    http = httplib2.Http()
    http.add_credentials(*(ogc_server_settings.credentials))
    headers = dict()

    if request.method in ("POST", "PUT") and "CONTENT_TYPE" in request.META:
        headers["Content-Type"] = request.META["CONTENT_TYPE"]

    response, content = http.request(
        url, request.method,
        body=request.raw_post_data or None,
        headers=headers)
        
    # we need to sync django here
    # we should remove this geonode dependence calling layers.views straigh
    # from GXP, bypassing the proxy
    if downstream_path == 'rest/styles' and len(request.raw_post_data)>0:
        # for some reason sometime gxp sends a put with empty request
        # need to figure out with Bart
        from geonode.layers import utils
        utils.style_update(request, url)

    return HttpResponse(
        content=content,
        status=response.status,
        mimetype=response.get("content-type", "text/plain"))


def picasa(request):
    url = "http://picasaweb.google.com/data/feed/base/all?thumbsize=160c&"
    kind = request.GET['kind'] if request.method == 'GET' else request.POST['kind']
    bbox = request.GET['bbox'] if request.method == 'GET' else request.POST['bbox']
    query = request.GET['q'] if request.method == 'GET' else request.POST['q']
    maxResults = request.GET['max-results'] if request.method == 'GET' else request.POST['max-results']
    coords = bbox.split(",")
    coords[0] = -180 if float(coords[0]) <= -180 else coords[0]
    coords[2] = 180 if float(coords[2])  >= 180 else coords[2]
    coords[1] = coords[1] if float(coords[1]) > -90 else -90
    coords[3] = coords[3] if float(coords[3])  < 90 else 90
    newbbox = str(coords[0]) + ',' + str(coords[1]) + ',' + str(coords[2]) + ',' + str(coords[3])
    url = url + "kind=" + kind + "&max-results=" + maxResults + "&bbox=" + newbbox + "&q=" + urllib.quote(query.encode('utf-8'))  #+ "&alt=json"

    feed_response = urllib.urlopen(url).read()
    return HttpResponse(feed_response, mimetype="text/xml")


def flickr(request):
    url = "http://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=%s" % settings.FLICKR_API_KEY
    bbox = request.GET['bbox'] if request.method == 'GET' else request.POST['bbox']
    query = request.GET['q'] if request.method == 'GET' else request.POST['q']
    maxResults = request.GET['max-results'] if request.method == 'GET' else request.POST['max-results']
    # coords = bbox.split(",")
    # coords[0] = -180 if float(coords[0]) <= -180 else coords[0]
    # coords[2] = 180 if float(coords[2])  >= 180 else coords[2]
    # coords[1] = coords[1] if float(coords[1]) > -90 else -90
    # coords[3] = coords[3] if float(coords[3])  < 90 else 90
    # newbbox = str(coords[0]) + ',' + str(coords[1]) + ',' + str(coords[2]) + ',' + str(coords[3])
    url = url + "&tags=%s&per_page=%s&has_geo=1&format=json&extras=geo,url_q&accuracy=1&nojsoncallback=1" % (query,maxResults)
    feed_response = urllib.urlopen(url).read()
    return HttpResponse(feed_response, mimetype="text/xml")


def hglpoints (request):
    from xml.dom import minidom
    import re
    url = HGL_URL + "/HGLGeoRSS?GeometryType=point"
    bbox = ["-180","-90","180","90"]
    max_results = request.GET['max-results'] if request.method == 'GET' else request.POST['max-results']
    if max_results is None:
        max_results = "100"
    try:
        bbox = request.GET['bbox'].split(",") if request.method == 'GET' else request.POST['bbox'].split(",")
    except:
        pass
    query = request.GET['q'] if request.method == 'GET' else request.POST['q']
    url = url + "&UserQuery=" + urllib.quote(query.encode('utf-8')) #+ \
        #"&BBSearchOption=1&minx=" + bbox[0] + "&miny=" + bbox[1] + "&maxx=" + bbox[2] + "&maxy=" + bbox[3]
    dom = minidom.parse(urllib.urlopen(url))
    iterator = 1
    for node in dom.getElementsByTagName('item'):
        if iterator <= int(max_results):
            description = node.getElementsByTagName('description')[0]
            guid = node.getElementsByTagName('guid')[0]
            title = node.getElementsByTagName('title')[0]
            if guid.firstChild.data != 'OWNER.TABLE_NAME':
                description.firstChild.data = description.firstChild.data + '<br/><br/><p><a href=\'javascript:void(0);\' onClick=\'app.addHGL("' \
                    + escape(title.firstChild.data) + '","' + re.sub("SDE\d?\.","", guid.firstChild.data)  + '");\'>Add to Map</a></p>'
            iterator +=1
        else:
            node.parentNode.removeChild(node)

    return HttpResponse(dom.toxml(), mimetype="text/xml")


def hglServiceStarter (request, layer):
    #Check if the layer is accessible to public, if not return 403
    accessUrl = HGL_URL + "/ogpHglLayerInfo.jsp?ValidationKey=" + settings.HGL_VALIDATION_KEY +"&layers=" + layer
    accessJSON = json.loads(urllib.urlopen(accessUrl).read())
    if accessJSON[layer]['access'] == 'R':
        return HttpResponse(status=403)

    #Call the RemoteServiceStarter to load the layer into HGL's Geoserver in case it's not already there
    startUrl = HGL_URL + "/RemoteServiceStarter?ValidationKey=" + settings.HGL_VALIDATION_KEY + "&AddLayer=" + layer
    return HttpResponse(urllib.urlopen(startUrl).read())


def tweetServerProxy(request,geopsip):
    url = urlsplit(request.get_full_path())
    if geopsip == "standard":
        geopsip = settings.GEOPS_IP
    tweet_url = "http://" + geopsip + "?" + url.query

    identifyQuery = re.search("QUERY_LAYERS", tweet_url)

    if identifyQuery is not None:
        if re.search("%20limit%2010", tweet_url)is None:
            return HttpResponse(status=403)

    step1 = urllib.urlopen(tweet_url)
    step2 = step1.read()
    if 'content-type' in step1.info().dict:
        response = HttpResponse(step2, mimetype= step1.info().dict['content-type'])
    else:
        response = HttpResponse(step2)
    try :
        cookie = step1.info().dict['set-cookie'].split(";")[0].split("=")[1]
        response.set_cookie("tweet_count", cookie)
    except:
        pass
    return response


def tweetDownload (request):

    if (not request.user.is_authenticated() or  not request.user.get_profile().is_org_member):
        return HttpResponse(status=403)

    proxy_url = urlsplit(request.get_full_path())
    download_url = "http://" + settings.GEOPS_IP + "?" + proxy_url.query  + settings.GEOPS_DOWNLOAD

    http = httplib2.Http()
    response, content = http.request(
        download_url, request.method)

    response =  HttpResponse(
        content=content,
        status=response.status,
        mimetype=response.get("content-type", "text/plain"))

    response['Content-Disposition'] = response.get('Content-Disposition', 'attachment; filename="tweets"' + request.user.username + '.csv');
    return response



def tweetTrendProxy (request):

    tweetUrl = "http://" + settings.AWS_INSTANCE_IP + "/?agg=trend&bounds=" + request.POST["bounds"] + "&dateStart=" + request.POST["dateStart"] + "&dateEnd=" + request.POST["dateEnd"];
    resultJSON =""
#    resultJSON = urllib.urlopen(tweetUrl).read()
#    import datetime
#
#
#    startDate = datetime.datetime.strptime(request.POST["dateStart"], "%Y-%b-%d")
#    endDate = datetime.datetime.strptime(request.POST["dateEnd"], "%Y-%b-%d")
#
#    recString = "record: ["
#
#    while startDate <= endDate:
#            recString += "{'date': '$date', 'Ebola$rnd5' : $rnd6, 'Malaria$rnd4' : $rnd7, 'Influenza$rnd3': $rnd8, 'Plague$rnd3': $rnd9, 'Lyme_Disease$rnd1': $rnd10},"
#            recString = recString.replace("$rnd6", str(random.randrange(50,500,1)))
#            recString = recString.replace("$rnd7", str(random.randrange(50,500,1)))
#            recString = recString.replace("$rnd8", str(random.randrange(50,500,1)))
#            recString = recString.replace("$rnd9", str(random.randrange(50,500,1)))
#            recString = recString.replace("$rnd10", str(random.randrange(50,500,1)))
#            recString = recString.replace("$date", datetime.datetime.strftime(startDate, '%b-%d-%Y'))
#            startDate = startDate + datetime.timedelta(days=1)
#
#    recString += "]"
#
#    resultJSON = """
#    {
#    metaData: {
#        root: "record",
#        fields: [
#            {name: 'date'},
#            {name: 'Ebola$rnd5'},
#            {name: 'Malaria$rnd4'},
#            {name: 'Influenza$rnd3'},
#            {name: 'Plague$rnd3'},
#            {name: 'Lyme_Disease$rnd1'}
#        ],
#    },
#    // Reader's configured root
#    $recString
#}
#"""
#
#    resultJSON = resultJSON.replace("$recString", recString)
#
#
#
#    resultJSON = resultJSON.replace("$rnd1", str(random.randrange(50,500,1)))
#    resultJSON = resultJSON.replace("$rnd2", str(random.randrange(50,500,1)))
#    resultJSON = resultJSON.replace("$rnd3", str(random.randrange(50,500,1)))
#    resultJSON = resultJSON.replace("$rnd4", str(random.randrange(50,500,1)))
#    resultJSON = resultJSON.replace("$rnd5", str(random.randrange(50,500,1)))

#    resultJSON = '{"metaData":{"fields":[{"name":"Tuberculosis"},{"name":"STD"},{"name":"Gastroenteritis"},{"name":"Influenza"},{"name":"Common_Cold"},{"name":"date"}],"root":"record"},"record":[{"Common_Cold":18,"Gastroenteritis":104,"Influenza":76,"STD":121,"Tuberculosis":236,"date":"2012-01-26"},{"Common_Cold":19,"Gastroenteritis":115,"Influenza":114,"STD":146,"Tuberculosis":397,"date":"2012-01-27"},{"Common_Cold":26,"Gastroenteritis":104,"Influenza":83,"STD":137,"Tuberculosis":402,"date":"2012-01-28"},{"Common_Cold":25,"Gastroenteritis":96,"Influenza":76,"STD":141,"Tuberculosis":358,"date":"2012-01-29"},{"Common_Cold":30,"Gastroenteritis":106,"Influenza":87,"STD":158,"Tuberculosis":372,"date":"2012-01-30"},{"Common_Cold":12,"Gastroenteritis":74,"Influenza":44,"STD":116,"Tuberculosis":222,"date":"2012-01-31"}]}'

    return HttpResponse(resultJSON, mimetype="application/json")

def youtube(request):
    url = "http://gdata.youtube.com/feeds/api/videos?v=2&prettyprint=true&"
    bbox = request.GET['bbox'] if request.method == 'GET' else request.POST['bbox']
    query = request.GET['q'] if request.method == 'GET' else request.POST['q']
    maxResults = request.GET['max-results'] if request.method == 'GET' else request.POST['max-results']
    coords = bbox.split(",")
    coords[0] = coords[0] if float(coords[0]) > -180 else -180
    coords[2] = coords[2] if float(coords[2])  < 180 else 180
    coords[1] = coords[1] if float(coords[1]) > -90 else -90
    coords[3] = coords[3] if float(coords[3])  < 90 else 90
    #location would be the center of the map.
    location = str((float(coords[3]) + float(coords[1]))/2)  + "," + str((float(coords[2]) + float(coords[0]))/2);

    #calculating the location-readius
    R = 6378.1370;
    PI = 3.1415926;
    left = R*float(coords[0])/180.0/PI;
    right = R*float(coords[2])/180.0/PI;
    radius = (right - left)/2*2;
    radius = 1000 if (radius > 1000) else radius;
    url = url + "location=" + location + "&max-results=" + maxResults + "&location-radius=" + str(radius) + "km&q=" + urllib.quote(query.encode('utf-8'))

    feed_response = urllib.urlopen(url).read()
    return HttpResponse(feed_response, mimetype="text/xml")

def download(request, service):
    

    h = httplib2.Http()
    GEOSERVER_USER, GEOSERVER_PASSWD = ogc_server_settings.USER, ogc_server_settings.PASSWORD
    h.add_credentials(GEOSERVER_USER, GEOSERVER_PASSWD)
    _netloc = urlparse(ogc_server_settings.DOWNLOAD_URL).netloc
    h.authorizations.append(httplib2.BasicAuthentication(
        (GEOSERVER_USER, GEOSERVER_PASSWD),
        _netloc,
        ogc_server_settings.DOWNLOAD_URL,
        {},
        None,
        None,
        h
        )
    )

    
    params = request.GET
    #mimetype = params.get("outputFormat") if service == "wfs" else params.get("format")

    url = ogc_server_settings.DOWNLOAD_URL + service + "?" + params.urlencode()
    layer = params["layers"] if "layers" in params else params["typename"]

    if "format" in params:
        format = params["format"]
    elif "outputFormat" in params:
        format = params["outputFormat"]
    elif "mode" in params:
        format = "kml"
    else:
        format = "unknown"

    if "/" in format:
        format = format.split("/")[1]

    format = format.replace("excel","xls").replace("gml2","xml")

    layer_obj = Layer.objects.get(typename=layer)

    if layer_obj.downloadable and request.user.has_perm('maps.view_layer', obj=layer_obj):

        layerstats,created = LayerStats.objects.get_or_create(layer=layer_obj)
        layerstats.downloads += 1
        layerstats.save()

        download_response, content = h.request(
            url, request.method,
            body=None,
            headers=dict())
        content_disposition = None
        if 'content_disposition' in download_response:
            content_disposition = download_response['content-disposition']
        mimetype = download_response['content-type']
        response = HttpResponse(content, mimetype = mimetype)
        if content_disposition is not None:
            response['Content-Disposition'] = content_disposition
        else:
            response['Content-Disposition'] = "attachment; filename=" + layer_obj.name + "." + format
        return response
    else:
        return HttpResponse(status=403)


def tweetServerProxy(request):
    url = urlsplit(request.get_full_path())
    tweet_url = "http://" + settings.GEOPS_IP + "?" + url.query

    step1 = urllib.urlopen(tweet_url)
    step2 = step1.read()
    response = HttpResponse(step2, mimetype= step1.info().dict['content-type'])
    try :
        cookie = step1.info().dict['set-cookie'].split(";")[0].split("=")[1]
        response.set_cookie("tweet_count", cookie)
    except:
        pass
    return response


def tweetDownload (request):

    if (not request.user.is_authenticated() or  not request.user.get_profile().is_org_member):
        return HttpResponse(status=403)

    proxy_url = urlsplit(request.get_full_path())
    download_url = "http://" + settings.GEOPS_IP + "?" + proxy_url.query  + settings.GEOPS_DOWNLOAD

    http = httplib2.Http()
    response, content = http.request(
        download_url, request.method)

    response =  HttpResponse(
        content=content,
        status=response.status,
        mimetype=response.get("content-type", "text/plain"))

    response['Content-Disposition'] = response.get('Content-Disposition', 'attachment; filename="tweets"' + request.user.username + '.csv');
    return response



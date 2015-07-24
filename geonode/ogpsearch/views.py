
from django.template import RequestContext, loader
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import render_to_response
from django.contrib.gis.geos import *
from geonode.maps.models import *
import pysolr
import math
import json

from geonode.maps.models import Layer
from geonode.maps.models import Map

from django.template import RequestContext, loader
from django.conf import settings
from geoserver.catalog import Catalog, FailedRequestError
from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService
from owslib.tms import TileMapService
from owslib.csw import CatalogueServiceWeb
from arcrest import Folder as ArcFolder, MapService as ArcMapService
from geonode.services.models import Service, Layer, ServiceLayer, WebServiceHarvestLayersJob, WebServiceRegistrationJob
from geonode.ogpsearch import utils

# passed a string array, 
def good_coords(coords):
    if (len(coords) != 4):
       return False;
    for coord in coords:
      try:
          num = float(coord)
          if (math.isnan(num)):
              return False
          if (math.isinf(num)):
              return False 
      except ValueError:
          return False
    return True

# from http://wiki.openstreetmap.org/wiki/Zoom_levels
# width of map in degrees when 256 pixels wide
zoom_level_to_degrees = {0: 360.0,
            1: 180.0,
            2: 90.0,
            3: 45.0,
            4: 22.5,
            5: 11.25,
            6: 5.625,
            7: 2.813,
            8: 1.406,
            9: 0.703,
            10: 0.352,
            11: 0.176,
            12: 0.088,
            13: 0.044,
            14: 0.022,
            15: 0.011,
            16: 0.005,
            17: 0.003,
            18: 0.001,
            19: 0.0005,
            20: 0.00025,
            21: 0.000015}

def ingest_solr_records():
    """test code to get Solr records them and add to SQL table"""
    # this function should be derived from services.views._register_cascaded_layers
    # and maps.utils.save and maps.models.resource
    # which is called during file upload from maps.views.upload_layer
    # but that is for local layers, we probably want to be a remote layer
    #remote_resource = LayerRemoteResource()
    #            remote_resource.metadata_links = zip(["text/xml"], ["TC211"], [settings.GEONETWORK_BASE_URL + \
    #                "srv/en/csw?" + urllib.urlencode({
    #                "request": "GetRecordById",
    #                "service": "CSW",
    #                "version": "2.0.2",
    #                "OutputSchema": "http://www.isotc211.org/2005/gmd",
    #                "ElementSetName": "full",
    #                "id": self.uuid
    #            })])
    #            remote_resource.resource_type = self.storeType
    #            self._resource_cache = remote_resource

    solr = pysolr.Solr('http://localhost:8983/solr/', timeout=10)
    results = solr.search("*:*", start=0)
    print "in solr_test"
    print results.hits
    docs = results.docs
    for doc in docs:
       solr_to_geonode_old(doc)


def solr_to_geonode_aux(doc):
    """create a geonode layer based on the passed solr record
    follows code in maps.views.upload_layer that deals with external layers
    """
    print 'display name: ', doc['LayerDisplayName']
    print '  layer id: ', doc['LayerId']
    print '  name : ' ,doc['Name']
    _user, _password = settings.GEOSERVER_CREDENTIALS

    location = json.loads(doc['Location'])
    wms_server_url = location['wms']
    if isinstance(wms_server_url, list):
        wms_server_url = wms_server_url[0]
    # wms_server_url = 'http://www.gaia-mv.de/dienste/DOP?REQUEST=GetCapabilities&VERSION=1.1.1&SERVICE=WMS'
    print '  wms_server_url: ', wms_server_url
    name = 'solr ' + doc['Name']
    title = 'solr ' + doc['LayerDisplayName']
    abstract = doc['Abstract']
    service = Service.objects.get_or_create(base_url = wms_server_url,
        type = "WFS",
        method='C',
        name = name,
        version = "1.1.1",
        title = title,
        abstract = abstract,
        online_resource = wms_server_url + doc['Name'],
        owner= None,
        parent = None)

    print '  service: ', service
    print '  settings.GEOSERVER_BASE_URL', settings.GEOSERVER_BASE_URL
    cat = Catalog(settings.GEOSERVER_BASE_URL + "rest",
                        _user , _password)
    print '  cat: ', cat
    print '  settings.CASCADE_WORKSPACE: ', settings.CASCADE_WORKSPACE

    try:
        cascade_ws = cat.get_workspace(settings.CASCADE_WORKSPACE)
        print ' try cascade success'
    except FailedRequestError:
        print ' cascade get failed, try cascade create'
        cascade_ws = cat.create_workspace(settings.CASCADE_WORKSPACE, "http://geonode.org/cascade")
    print '  cascade: ', cascade_ws

    try:
        store = cat.get_store(service.name,cascade_ws)
    except Exception:
        store = cat.create_wmsstore(service.name, cascade_ws)
    print '  store: ', store
    parent_layer = Layer()
    resource = cat.create_wfslayer(cascade_ws, store, parent_layer)

    cascaded_layer, created = Layer.objects.get_or_create(name=resource.name, service=service,
                        defaults = {
                            "workspace": cascade_ws.name,
                            "store": store.name,
                            "storeType": store.resource_type,
                            "typename": "%s:%s" % (cascade_ws.name, resource.name),
                            "title": resource.title or 'No title provided',
                            "abstract": resource.abstract or 'No abstract provided',
                            "owner": None,
                            "uuid": str(uuid.uuid4()),
                            "service": service
                        })
    print '  created: ', created
    print '  cascaded_layer: ', cascaded_layer

def solr_to_geonode_aux_old(doc):
    """creates geonode layer based on Solr record
    creating a row in the Layer table isn't sufficient.  this code
    was based on local layer code in needs to look like code in maps.views.upload_layer.
    It should follow services.views._register_cascaded_layers
    that deals with external layers

    """
    layer = Layer()
    location = json.loads(doc['Location'])
    wms_server = location['wms']
    if isinstance(wms_server, list):
        wms_server = wms_server[0]
    print '  wms server: ' , wms_server
    remote_resource = LayerRemoteResource()
    remote_resource.metadata_links = zip(["text/xml"], ["TC211"],
                           [wms_server + "srv/en/csw?" + urllib.urlencode({
                            "request": "GetRecordById",
                            "service": "CSW",
                            "version": "2.0.2",
                            "OutputSchema": "http://www.isotc211.org/2005/gmd",
                            "ElementSetName": "full",
                            "id": doc['Name']
                        })])
    remote_resource.resource_type = 'remoteStore'
    layer._resource_cache = remote_resource
    layer.title = 'solr ' + doc['LayerDisplayName']
    layer.uuid = 'solr_' + doc['LayerId']
    layer.service = None
    abstract = doc['Abstract']
    if not abstract:
        abstract = "No abstract in Solr record"
    layer.abstract = doc['Abstract']
    layer.downloadable = True
    layer.llbbox = [doc['MinX'], doc['MinY'], doc['MaxX'], doc['MaxY']]
    layer.bbox = [doc['MinX'], doc['MinY'], doc['MaxX'], doc['MaxY']]
    layer.srs = 'EPSG:900913'
    layer.save()
    layer.keywords.add('remote')
    print '  ', doc['ThemeKeywords']
    # layer.keywords.add(doc['ThemeKeywords'])
    keywords = doc['ThemeKeywords'].split()
    for keyword in keywords:
        layer.keywords.add(keyword)
    # set to a public layer, need to verify it really is public
    if doc['Access'] == 'Public':
        layer.set_default_permissions()
    layer.save()
    print '  download links: ', layer.download_links()


def ingest_maps():
    """create Solr records of map objects in sql database"""
    maps = Map.objects.all()
    print "number of maps from sql", len(maps)
    #if (len(maps) > 0):
    #    return
    solr = pysolr.Solr('http://localhost:8983/solr/', timeout=10)
    i = 0
    for map in maps:
        i = i + 1
        center_x = map.center_x
        center_y = map.center_y
        projection = map.projection # EPSG:900913
        srid = projection.replace("EPSG:", "SRID=")
        # we need something like GEOSGeometry('SRID=2029;POINT(630084 4833438)')
        center = GEOSGeometry(srid + ";POINT(" + str(center_x) + " " + str(center_y) + ")")
        center.transform(4326)   # Transform to WGS84
        center_longitude = center.x
        center_latitude = center.y
        zoom_level = map.zoom
        if (zoom_level > 21):
            print "clipped zoom", map.title, zoom_level
            zoom_level = 21
        width_degrees = zoom_level_to_degrees[zoom_level]
        minX = center_longitude - (width_degrees / 2.0)
        maxX = center_longitude + (width_degrees / 2.0)
        minY = center_latitude - (width_degrees / 2.0)
        maxY = center_latitude + (width_degrees / 2.0)
        halfWidth = width_degrees / 2.0
        halfHeight = width_degrees / 2.0
        area = (halfWidth * 2) * (halfHeight * 2)
        print "map: ", zoom_level, width_degrees, map.projection, map.title, center_latitude, center_longitude
        solr.add([{"LayerId": "HarvardWorldMap_" + str(i),
                   "Name": map.title,
                   "LayerDisplayName": map.title,
                   "Institution": "Harvard",
                   "Publisher": "Harvard",
                   "Originator": "Harvard",
                   "Access": "Public",
                   "DataType": "Polygon",
                   "Location": "{}",
                   "Abstract": "abstract",
                   "SrsProjectionCode": "",
                   "MinY": minY,
                   "MinX": minX,
                   "MaxY": maxY,
                   "MaxX": maxX,
                   "CenterY": center_latitude,
                   "CenterX": center_longitude,
                   "HalfWidth": halfWidth,
                   "HalfHeight": halfHeight,
                   "Area": area}])


# "{\"wms\": [\"http://geoserver01.uit.tufts.edu/wms\"],\"wfs\": \"http://geoserver01.uit.tufts.edu/wfs\"}"
def ingest_layers():
    """create Solr records of layer objects in sql database"""
    layers = Layer.objects.all()
    #layers = [layers[0]]  # just the first
    i = 1
    solr = pysolr.Solr('http://localhost:8983/solr/ogpsearch', timeout=10)
    for layer in layers:
        print "layer:", layer.title, layer.distribution_url, layer.distribution_description, layer.store
        bbox = layer.llbbox
        if (isinstance(bbox, basestring)):
            bbox = bbox.replace('[', '')
            bbox = bbox.replace(']', '')
            coords = bbox.split(',')
            print "coords: ", coords
            if (good_coords(coords)):
                minX = float(coords[0])
                minY = float(coords[1])
                maxX = float(coords[2])
                maxY = float(coords[3])
                centerY = (maxY + minY) / 2.0
                centerX = (maxX + minX) / 2.0
                halfWidth = (maxY - minY) / 2.0
                halfHeight = (maxX - minX) / 2.0
                area = (halfWidth * 2) * (halfHeight * 2)
                #ENVELOPE(minX, maxX, maxY, minY) per https://github.com/spatial4j/spatial4j/issues/36
                wkt = "ENVELOPE({:f},{:f},{:f},{:f})".format(minX, maxX, maxY, minY)
                print ('wkt: ', wkt)
                solr.add([{"LayerId": "HarvardWorldMapLayer_" + str(i),  # layer.uuid,
                           "Name": layer.title,  # "Zipcodes Somerville MA 2006", # layer.title,
                           "LayerDisplayName": layer.title,
                           "Institution": "Tufts",  # "Harvard",
                           "Publisher": "Harvard",
                           "Originator": "Harvard",
                           "Access": "Public",
                           "DataType": "Polygon",
                           "Availability": "Online",
                           "Location": '{"wms": ["http://geoserver01.uit.tufts.edu/wms"],"wfs": "http://geoserver01.uit.tufts.edu/wfs",' \
                                       +' "workspace": "' + layer.workspace + '", "store": "' + layer.store + '",' \
                                        ' "storeType": "' + layer.storeType + '", "name": "' + layer.name + '"}',
                           "Abstract": "abstract",
                           "SrsProjectionCode": "",
                           "MinY": minY,
                           "MinX": minX,
                           "MaxY": maxY,
                           "MaxX": maxX,
                           "CenterY": centerY,
                           "CenterX": centerX,
                           "HalfWidth": halfWidth,
                           "HalfHeight": halfHeight,
                           "Area": area,
                           "bbox_rpt": wkt}])
                i = i+1
    print 'geonode to layers processed ', i-1


def index(request):
    # ingest_maps()
    # ingest_layers()
    #solr_test()
    extra_context = {'SOLR_URL': settings.get('SOLR_URL', 'http://localhost:8983/solr/geonode24')}
    return render_to_response('ogpsearch/ogpsearch.html', RequestContext(request, extra_context))

def geonode_to_solr(request):
    utils.OGP_utils.geonode_to_solr()
    # ingest_layers()
    return render_to_response('ogpsearch/geonode_to_solr.html', RequestContext(request))

def solr_to_geonode(request):
    ingest_solr_records()
    return render_to_response('ogpsearch/solr_to_geonode.html', RequestContext(request))


from django.template import RequestContext, loader
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import render_to_response
from django.contrib.gis.geos import *
import pysolr
import math

from geonode.maps.models import Layer
from geonode.maps.models import Map

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

def ingest_maps():
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
    layers = Layer.objects.all()
    #layers = [layers[0]]  # just the first
    i = 1
    solr = pysolr.Solr('http://localhost:8983/solr/', timeout=10)
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
                solr.add([{"LayerId": "HarvardWorldMapLayer_" + str(i),  # layer.uuid,
                           "Name": "Zipcodes Somerville MA 2006", # layer.title,
                           "LayerDisplayName": layer.title,
                           "Institution": "Tufts",  # "Harvard",
                           "Publisher": "Harvard",
                           "Originator": "Harvard",
                           "Access": "Public",
                           "DataType": "Polygon",
                           "Availability": "Online",
                           "Location": '{"wms": ["http://geoserver01.uit.tufts.edu/wms"],"wfs": "http://geoserver01.uit.tufts.edu/wfs"}',
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
                           "Area": area}])
                i = i+1


def index(request):
    # ingest_maps()
    # ingest_layers()
    return render_to_response('ogpsearch/ogpsearch.html', RequestContext(request))


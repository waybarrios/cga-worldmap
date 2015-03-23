
import pysolr
import math
import json

from geonode.maps.models import Layer
from geonode.maps.models import Map

from django.conf import settings
from geoserver.catalog import Catalog, FailedRequestError
from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService
from owslib.tms import TileMapService
from owslib.csw import CatalogueServiceWeb
from arcrest import Folder as ArcFolder, MapService as ArcMapService
from geonode.services.models import Service, Layer, ServiceLayer, WebServiceHarvestLayersJob, WebServiceRegistrationJob

class OGP_utils(object):

    @staticmethod
    def good_coords(coords):
        """ passed a string array """
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

    solr = pysolr.Solr('http://localhost:8983/solr/ogpsearch', timeout=10)


    @staticmethod
    def layer_to_solr(layer, i=0):
        try:
            bbox = layer.llbbox
            bbox = bbox.replace('[', '')
            bbox = bbox.replace(']', '')
            coords = bbox.split(',')
            print "coords: ", coords
            if (OGP_utils.good_coords(coords)):
                minX = float(coords[0])
                minY = float(coords[1])
                maxX = float(coords[2])
                maxY = float(coords[3])
                centerY = (maxY + minY) / 2.0
                centerX = (maxX + minX) / 2.0
                halfWidth = (maxY - minY) / 2.0
                halfHeight = (maxX - minX) / 2.0
                area = (halfWidth * 2) * (halfHeight * 2)
                # ENVELOPE(minX, maxX, maxY, minY) per https://github.com/spatial4j/spatial4j/issues/36
                wkt = "ENVELOPE({:f},{:f},{:f},{:f})".format(minX, maxX, maxY, minY)
                print ('wkt: ', wkt)
                if (i == 0):
                    i = layer.title
                OGP_utils.solr.add([{"LayerId": "HarvardWorldMapLayer_" + str(i),  # layer.uuid,
                                 "Name": layer.title,  # "Zipcodes Somerville MA 2006", # layer.title,
                                 "LayerDisplayName": layer.title,
                                 "Institution": "Tufts",  # "Harvard",
                                 "Publisher": "Harvard",
                                 "Originator": "Harvard",
                                 "Access": "Public",
                                 "DataType": "Polygon",
                                 "Availability": "Online",
                                 "Location": '{"wms": ["http://geoserver01.uit.tufts.edu/wms"],"wfs": "http://geoserver01.uit.tufts.edu/wfs",' \
                                             + ' "workspace": "' + layer.workspace + '", "store": "' + layer.store + '",' \
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
        except Exception as e:
            print("error adding solr doc: " + e.message)

    @staticmethod
    def geonode_to_solr():
        """create Solr records of layer objects in sql database"""
        layers = Layer.objects.all()
        layers = [layers[0]]  # just the first
        i = 1

        for layer in layers:
            print "layer:", layer.title, layer.distribution_url, layer.distribution_description, layer.store
            bbox = layer.llbbox
            if (isinstance(bbox, basestring)):
                OGP_utils.layer_to_solr(bbox, i, layer)
                i = i+1
        print 'geonode to layers processed ', i-1


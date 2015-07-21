
import pysolr
import math
import json

import geonode.maps.models

from django.conf import settings
from geoserver.catalog import Catalog, FailedRequestError
from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService
from owslib.tms import TileMapService
from owslib.csw import CatalogueServiceWeb
from arcrest import Folder as ArcFolder, MapService as ArcMapService
import logging
import time
from geonode.layers.models import Layer
from urlparse import urlparse

#from geonode.services.models import Service, Layer, ServiceLayer, WebServiceHarvestLayersJob, WebServiceRegistrationJob

class OGP_utils(object):

    @staticmethod
    def good_coords(coords):
        """ passed a string array """
        if (len(coords) != 5):
            return False;
        for coord in coords[0:3]:
            try:
                num = float(coord)
                if (math.isnan(num)):
                    return False
                if (math.isinf(num)):
                    return False
            except ValueError:
                return False
        return True

    solr = pysolr.Solr('http://localhost:8983/solr/geonode24', timeout=60)
    logger = logging.getLogger("geonode.ogpsearch.utils")



    @staticmethod
    def get_domain(url):
        urlParts = urlparse(url)
        hostname = urlParts.hostname
        if hostname == "localhost":
            return "Harvard" # assumption
        domainParts = hostname.split(".")
        if len(domainParts) == 1:
            return domainParts[0]
        return domainParts[-2].capitalize()
        

    @staticmethod
    def layer_to_solr(layer, i=0):
        try:
            bbox = layer.bbox
            if (OGP_utils.good_coords(bbox) == False):
                print 'no coords in layer ', layer.title
                return

            if (OGP_utils.good_coords(bbox)):
                print 'in utils.layer_to_solr, bbox = ', bbox
                minX = float(bbox[0])
                minY = float(bbox[1])
                maxX = float(bbox[2])
                maxY = float(bbox[3])
                projection = bbox[4]
                if (minY > maxY):
                    tmp = minY
                    minY = maxY
                    maxY = tmp
                if (minX > maxX):
                    tmp = minX
                    minX = maxX
                    maxX = tmp
                centerY = (maxY + minY) / 2.0
                centerX = (maxX + minX) / 2.0
                halfWidth = (maxX - minX) / 2.0
                halfHeight = (maxY - minY) / 2.0
                area = (halfWidth * 2) * (halfHeight * 2)
                # ENVELOPE(minX, maxX, maxY, minY) per https://github.com/spatial4j/spatial4j/issues/36
                wkt = "ENVELOPE({:f},{:f},{:f},{:f})".format(minX, maxX, maxY, minY)
                dataType = "Raster"
                if (layer.is_vector()):
                    dataType = "Polygon"
                institution = "Harvard"
                if layer.storeType == "remoteStore":
                    institution = "Remote"
                owsUrl = layer.ows_url
                domain = OGP_utils.get_domain(owsUrl)
                if (i == 0):
                    i = layer.title
                #if domain != "Harvard":
                #    dataType = "Remote"
                OGP_utils.solr.add([{"LayerId": "HarvardWorldMapLayer_" + str(i), 
                                 "Name": layer.title,  
                                 "LayerDisplayName": layer.title,
                                 "Institution": domain,
                                 "Publisher": "Harvard",
                                 "Originator": domain,
                                 "Access": "Public",
                                 "DataType": dataType, 
                                 "Availability": "Online",
                                 "Location": '{"layerInfoPage": "' + layer.get_absolute_url() + '"}',
                                 "Abstract": "abstract",
                                 "SrsProjectionCode": projection,
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
                OGP_utils.logger.error("solr record saved: " + layer.title)
        except Exception as e:
            OGP_utils.logger.error("error in layer_to_solr processing layer: " + e.message)

    @staticmethod
    def geonode_to_solr():
        """create Solr records of layer objects in sql database"""
        layers = Layer.objects.all()
        print "original number of layers = ", len(layers)
        # layers = [layers[0]]  # just the first
        i = 1
        for layer in layers:
            bbox = layer.bbox
            #if (layer.upload_session):
            #    print '  ', layer.upload_session.processed, layer.upload_session.context
            OGP_utils.layer_to_solr(layer, i)
            i = i+1
            time.sleep(.1)

        OGP_utils.solr.optimize()
        print 'geonode to layers processed ', i-1

    @staticmethod
    def solr_to_solr():
        """create Solr records for layers in another Solr OGP instance"""
        ogp_solr = pysolr.Solr('http://geodata.tufts.edu/solr/')
        wm_solr = pysolr.Solr('http://localhost:8983/solr/all', timeout=60)
        count = 3200;
        while (True):
            docs = ogp_solr.search("*:*", start=count)
            count += len(docs)
            if (len(docs) == 0):
                return
            time.sleep(1)
            print "count = ", count
            for doc in docs:
                minX = doc['MinX']
                minY = doc['MinY']
                maxX = doc['MaxX']
                maxY = doc['MaxY']
                wkt = "ENVELOPE({:f},{:f},{:f},{:f})".format(minX, maxX, maxY, minY)
                if (-90 <= minY <= 90 and -90 <= maxY <= 90 and -180 <= minX <= 180 and -180 <= maxX <=180):
                    try:
                        wm_solr.add([{"LayerId": doc['LayerId'],
                                 "Name": doc['Name'],
                                 "LayerDisplayName": doc['LayerDisplayName'],
                                 "Institution": "OGP-" + doc['Institution'],  # "Harvard",
                                 "Publisher": doc['Publisher'],
                                 "Originator": doc['Originator'],
                                 "Access": 'Public',
                                 "DataType": doc['DataType'],
                                 "Availability": doc['Availability'],
                                 "Location": doc['Location'],
                                 "Abstract": doc['Abstract'],
                                 "MinY": doc['MinY'],
                                 "MinX": doc['MinX'],
                                 "MaxY": doc['MaxY'],
                                 "MaxX": doc['MaxX'],
                                 "CenterY": doc['CenterY'],
                                 "CenterX": doc['CenterX'],
                                 "HalfWidth": doc['HalfWidth'],
                                 "HalfHeight": doc['HalfHeight'],
                                 "Area": doc['Area'],
                                 "bbox_rpt": wkt}])
                    except KeyError as e:
                        print doc['LayerDisplayName', e]
                else:
                    print "bad bounds: ", doc





        

        


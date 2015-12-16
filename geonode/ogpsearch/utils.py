
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
from datetime import datetime
import re
import requests
from geonode.layers.models import Layer
from urlparse import urlparse

from geonode.services.models import Service

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

    solr_url = getattr(settings, 'SOLR_URL', 'http://localhost:8983/solr/geonode24')
    solr = pysolr.Solr(solr_url, timeout=60)
    logger = logging.getLogger("geonode.ogpsearch.utils")



    @staticmethod
    def get_domain(url):
        urlParts = urlparse(url)
        hostname = urlParts.hostname
        if hostname == "localhost":
            return "Harvard" # assumption
        return hostname
    @staticmethod
    def extract_date(layer):
        year = re.search('\d{4}', layer.title)
        if year is None:
            year = re.search('\d{4}', layer.abstract)
        if year is not None:
            year = year.group(0).strip()
            year = year.strip()
            year = int(year)
            if (year < 1000 or year > datetime.now().year):
                year = None
            else:
                year = datetime(year=year,month=1,day=1)
        return year
    @staticmethod
    def is_solr_up():
        solr_url = getattr(settings, 'SOLR_URL', 'http://localhost:8983/solr/geonode24')
        solr_url_parts = solr_url.split('/')
        core = solr_url_parts[-1]
        admin_url = '/'.join(solr_url_parts[:-1]) + '/admin/cores'
        params = {'action': 'STATUS','wt':'json'}
        try:
            req = requests.get(admin_url,params=params)
            response = json.loads(req.text)
            status = response['status']
            response = True
        except requests.exceptions.RequestException as e:
            response = False
        return response
            
        

    @staticmethod
    def layer_to_solr(layer, i=0):
        try:
            bbox = layer.bbox
            date = layer.temporal_extent_start
            if date is None:
                date = OGP_utils.extract_date(layer)
                if date is None:
                    date = layer.date 
            if (OGP_utils.good_coords(bbox) == False):
                print 'no coords in layer ', layer.title
                return
            if (OGP_utils.good_coords(bbox)):
                print 'in utils.layer_to_solr, bbox = ', bbox
                username = ""
                if (layer.owner):
                    username = layer.owner.username
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
                if (minX < -180):
                    minX = -180
                if (maxX > 180):
                    maxX = 180
                if (minY < -90):
                    minY = -90
                if (maxY > 90):
                    maxY = 90
                # ENVELOPE(minX, maxX, maxY, minY) per https://github.com/spatial4j/spatial4j/issues/36
                wkt = "ENVELOPE({:f},{:f},{:f},{:f})".format(minX, maxX, maxY, minY)
                dataType = "Raster"
                if (layer.is_vector()):
                    dataType = "Polygon"
                institution = "Harvard"
                servicetype = None;
                owsUrl = layer.ows_url
                if layer.storeType == "remoteStore":
                    institution = "Remote"
                    servicetype = Service.objects.get(base_url=owsUrl).type
                    if servicetype == "REST":
                        dataType = "RESTServices"
                    else:
                        dataType = "WMSServices"
                domain = OGP_utils.get_domain(owsUrl)
                if (i == 0):
                    i = layer.title
                OGP_utils.solr.add([{"LayerId": "HarvardWorldMapLayer_" + str(i), 
                                 "Name": layer.title,  
                                 "LayerDisplayName": layer.title,
                                 "Institution": institution,
                                 "Publisher": username,
                                 "Originator": domain,
                                 "ServiceType": servicetype,
                                 "ContentDate": date,
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
            if e.message.startswith("Connection") or e.message.startswith("[Reason: java.lang.OutOfMemoryError:"):
                OGP_utils.solr.add([{"LayerId": "HarvardWorldMapLayer_" + str(i),
                                 "Name": layer.title,
                                 "LayerDisplayName": layer.title,
                                 "Institution": institution,
                                 "Publisher": username,
                                 "Originator": domain,
                                 "ServiceType": servicetype,
                                 "ContentDate": date,
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
                                 }])
                OGP_utils.logger.error("failed solr record saved after retry: " + layer.title)
            else:
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
                                 "ContentDate": doc['ContentDate'],
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





        

        


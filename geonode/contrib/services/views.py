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
import urllib

import uuid
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext, loader
from django.utils.translation import ugettext as _
import json
from django.shortcuts import get_object_or_404


#from geonode.core.layers.views import layer_set_permissions
from geoserver.catalog import Catalog
from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService
from owslib.tms import TileMapService
from owslib.csw import CatalogueServiceWeb
from arcrest import Folder as ArcFolder, MapService as ArcMapService
from urlparse import urlsplit, urlunsplit


#from geonode.utils import OGC_Servers_Handler
from geonode.contrib.services.models import Service, Layer, ServiceLayer, WebServiceHarvestLayersJob, WebServiceRegistrationJob
from geonode.maps.views import _perms_info, bbox_to_wkt
from geonode.core.models import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.contrib.services.forms import CreateServiceForm, ServiceLayerFormSet, ServiceForm
from geonode.utils import slugify
import re
from geonode.maps.utils import llbbox_to_mercator, mercator_to_llbbox
from django.db import transaction

logger = logging.getLogger("geonode.core.layers.views")


#ogc_server_settings = OGC_Servers_Handler(settings.OGC_SERVER)['default']

_user, _password = settings.GEOSERVER_CREDENTIALS #ogc_server_settings.credentials

SERVICE_LEV_NAMES = {
    Service.LEVEL_NONE  : _('No Service Permissions'),
    Service.LEVEL_READ  : _('Read Only'),
    Service.LEVEL_WRITE : _('Read/Write'),
    Service.LEVEL_ADMIN : _('Administrative')
}

@login_required
def services(request):
    """
    This view shows the list of all registered services
    """
    services = Service.objects.all()
    return render_to_response("services/service_list.html", RequestContext(request, {
        'services': services,
    }))

@login_required
def register_service(request):
    """
    This view is used for manually registering a new service, with only URL as a
    parameter.
    """

    if request.method == "GET":
        service_form = CreateServiceForm()
        return render_to_response('services/service_register.html',
                                  RequestContext(request, {
                                      'create_service_form': service_form
                                  }))

    elif request.method == 'POST':
        # Register a new Service
        service_form = CreateServiceForm(request.POST)
        try:
            url = _clean_url(request.POST.get('url'))

            # method = request.POST.get('method')
            # type = request.POST.get('type')
            # name = slugify(request.POST.get('name'))

            type = _verify_service_type(url)

            if type is None:
                return HttpResponse('Could not determine server type', status = 400)

            if "user" in request.POST and "password" in request.POST:
                user = request.POST.get('user')
                password = request.POST.get('password')
            else:
                user = None
                password = None

            if type == "WMS" or type == "OWS":
                return _process_wms_service(url, type, user, password, owner=request.user)
            elif type == "REST":
                return _register_arcgis_url(url, user, password, owner=request.user)
            elif type == "OGP":
                return harvest_ogp_service(url)
            else:
                return HttpResponse('Not Implemented (Yet)', status=501)
        except Exception, e:
            logger.error("Unexpected Error", exc_info=1)
            return HttpResponse('Unexpected Error: %s' % e, status=500)
    elif request.method == 'PUT':
        # Update a previously registered Service
        return HttpResponse('Not Implemented (Yet)', status=501)
    elif request.method == 'DELETE':
        # Delete a previously registered Service
        return HttpResponse('Not Implemented (Yet)', status=501)
    else:
        return HttpResponse('Invalid Request', status = 400)

def _is_unique(url):
    """
    Determine if a service is already registered based on matching url
    """
    try:
        service = Service.objects.get(base_url=url)
        return False
    except Service.DoesNotExist:
        return True

def _clean_url(base_url):
    """
    Remove all parameters from a URL
    """
    urlprop = urlsplit(base_url)
    url = urlunsplit((urlprop.scheme, urlprop.netloc, urlprop.path, None, None))
    return url

def _get_valid_name(proposed_name):
    """
    Return a unique slug name for a service
    """
    slug_name = slugify(proposed_name)
    name = slug_name
    if len(slug_name)>40:
        name = slug_name[:40]
    existing_service = Service.objects.filter(name=name)
    iter = 1
    while existing_service.count() > 0:
        name = slug_name + str(iter)
        existing_service = Service.objects.filter(name=name)
        iter+=1
    return name

def _verify_service_type(base_url, type=None):
    """
    Try to determine service type by process of elimination
    """

    if type in ["WMS", "OWS", None]:
        try:
            service = WebMapService(base_url)
            service_type = 'WMS'
            try:
                servicewfs = WebFeatureService(base_url)
                service_type = 'OWS'
            except:
                pass
            return service_type
        except:
            pass
    if type in ["TMS",None]:
        try:
            service = TileMapService(base_url)
            return "TMS"
        except:
            pass
    if type in ["REST", None]:
        try:
            service = ArcFolder(base_url)
            service.services
            return "REST"
        except:
            pass
    if type in ["CSW", None]:
        try:
            service = CatalogueServiceWeb(base_url)
            return "CSW"
        except:
            pass
    if type in ["OGP", None]:
        #Just use a specific OGP URL for now
        if base_url == settings.OGP_URL:
            return "OGP"
        return None

def register_service_by_type(request):
    """
    Register a service based on a specified type
    """
    url = request.POST.get("url")
    type = request.POST.get("type")

    try:
        url = _clean_url(url)
        service = Service.objects.get(base_url=url)
        return
    except:
        type = _verify_service_type(url, type)

        if type == "WMS" or type == "OWS":
            return _process_wms_service(url, type, None, None)
        elif type == "REST":
            return _process_arcgis_service(url, None, None)

def _process_wms_service(url, type, username, password, owner=None):
    """
    Create a new WMS/OWS service, cascade it if necessary
    """
    server = WebMapService(url)
    try:
        base_url = _clean_url(server.getOperationByName('GetMap').methods['Get']['url'])

        if base_url and base_url != url:
            url = base_url
            server = WebMapService(base_url)
    except:
        logger.info("Could not retrieve GetMap url, using originally supplied URL %s" % url)
        pass

    try:
        service = Service.objects.get(base_url=url)
        return_dict = {}
        return_dict['service_id'] = service.pk
        return_dict['msg'] = "This is an existing Service"
        return HttpResponse(json.dumps(return_dict),
                            mimetype='application/json',
                            status=200)
    except:
        pass

    title = server.identification.title
    if title:
        name = _get_valid_name(title)
    else:
        name = _get_valid_name(urlsplit(url).netloc)
    try:
        supported_crs  = ','.join(server.contents.itervalues().next().crsOptions)
    except:
        supported_crs = None
    if re.search('EPSG:900913|EPSG:3857', supported_crs):
        return _register_indexed_service(type, url, name, username, password, wms=server, owner=owner)
    else:
        return _register_cascaded_service(type, url, name, username, password, wms=server, owner=owner)

def _register_cascaded_service(url, type, name, username, password,  wms=None, owner=None):
    """
    Register a service as cascading WMS
    """
    if type == 'WMS':
        # Register the Service with GeoServer to be cascaded
        cat = Catalog(settings.GEOSERVER_BASE_URL + "rest", 
                        _user , _password)
        # Can we always assume that it is geonode?
        geonode_ws = cat.get_workspace("geonode")
        ws = cat.create_wmsstore(name,geonode_ws, username, password)
        ws.capabilitiesURL = url
        ws.type = "WMS"
        cat.save(ws)
        available_resources = ws.get_resources(available=True)
        
        # Save the Service record
        service = Service(type = type,
                            method='C',
                            base_url = url,
                            name = name,
                            owner = owner)
        service.save()
        message = "Service %s registered" % service.name
        return_dict = {'status': 'ok', 'msg': message, 
                        'id': service.pk,
                        'available_layers': available_resources}
        return HttpResponse(json.dumps(return_dict), 
                            mimetype='application/json',
                            status=200)        
    elif type == 'WFS':
        # Register the Service with GeoServer to be cascaded
        cat = Catalog(settings.GEOSERVER_BASE_URL + "rest", 
                        _user , _password)
        # Can we always assume that it is geonode?
        geonode_ws = cat.get_workspace("geonode")
        wfs_ds = cat.create_datastore(name)
        connection_params = {
            "WFSDataStoreFactory:MAXFEATURES": "0",
            "WFSDataStoreFactory:TRY_GZIP": "true",
            "WFSDataStoreFactory:PROTOCOL": "false",
            "WFSDataStoreFactory:LENIENT": "true",
            "WFSDataStoreFactory:TIMEOUT": "3000",
            "WFSDataStoreFactory:BUFFER_SIZE": "10",
            "WFSDataStoreFactory:ENCODING": "UTF-8",
            "WFSDataStoreFactory:WFS_STRATEGY": "nonstrict",
            "WFSDataStoreFactory:GET_CAPABILITIES_URL": url,
        }
        if username and password:
            connection_params["WFSDataStoreFactory:USERNAME"] = username
            connection_params["WFSDataStoreFactory:PASSWORD"] = password

        wfs_ds.connection_parameters = connection_params
        cat.save(wfs_ds)
        available_resources = wfs_ds.get_resources(available=True)
        
        # Save the Service record
        service = Service(type = type,
                            method='C',
                            base_url = url,
                            name = name,
                            owner = owner)
        service.save()
        message = "Service %s registered" % service.name
        return_dict = {'status': 'ok', 'msg': message, 
                        'id': service.pk,
                        'available_layers': available_resources}
        return HttpResponse(json.dumps(return_dict), 
                            mimetype='application/json',
                            status=200)        
    elif type == 'WCS':
        return HttpResponse('Not Implemented (Yet)', status=501)
    else:
        return HttpResponse(
            'Invalid Method / Type combo: ' + 
            'Only Cascaded WMS, WFS and WCS supported',
            mimetype="text/plain",
            status=400)

def _register_cascaded_layers(service, perm_spec, verbosity=False, owner=None):
    """
    Register layers for a cascading WMS
    """
    if service.type == 'WMS' or service.type == "WFS":
        cat = Catalog(settings.GEOSERVER_BASE_URL + "rest", 
                        _user , _password)
        # Can we always assume that it is geonode? 
        geonode_ws = cat.get_workspace("geonode") 
        store = cat.get_store(service.name,geonode_ws)

        wms = WebMapService(service.base_url)
        layers = list(wms.contents)

        count = 0
        for layer in layers: 
            lyr = cat.get_resource(layer.name, store, geonode_ws)
            if(lyr == None):
                if service.type == "WMS":
                    resource = cat.create_wmslayer(geonode_ws, store, layer)
                elif service.type == "WFS":
                     resource = cat.create_wfslayer(geonode_ws, store, layer)
                if resource:
                    new_layer, status = Layer.objects.save_layer_from_geoserver(geonode_ws,
                                                        store, resource)
                    new_layer.owner = owner
                    new_layer.save()
                    if perm_spec:
                        #layer_set_permissions(new_layer, perm_spec)
                        pass
                    else:
                        pass # Will be assigned default perms
                    count += 1
        message = "%d Layers Registered" % count
        return_dict = {'status': 'ok', 'msg': message }
        return HttpResponse(json.dumps(return_dict),
                            mimetype='application/json',
                            status=200)
    elif service.type == 'WCS':
        return HttpResponse('Not Implemented (Yet)', status=501)
    else:
        return HttpResponse('Invalid Service Type', status=400)

def _register_indexed_service(type, url, name, username, password, verbosity=False, wms=None, owner=None):
    """
    Register a service - WMS or OWS currently supported
    """
    if type in ['WMS',"OWS","HGL"]:
        # TODO: Handle for errors from owslib
        if wms is None:
            wms = WebMapService(url)
        # TODO: Make sure we are parsing all service level metadata
        # TODO: Handle for setting ServiceContactRole
        service, created = Service.objects.get_or_create(base_url = url)
        if created:
            service.type = type
            service.method='I'
            service.name = name
            service.version = wms.identification.version
            service.title = wms.identification.title
            service.abstract = wms.identification.abstract
            service.keywords = ','.join(wms.identification.keywords)
            service.online_resource = wms.provider.url
            service.owner=owner
            service.save()

            available_resources = []
            for layer in list(wms.contents):
                available_resources.append([wms[layer].name, wms[layer].title])

        if settings.USE_QUEUE:
            #Create a layer import job
            WebServiceHarvestLayersJob.objects.get_or_create(service=service)
        else:
            _register_indexed_layers(service, wms=wms, owner=owner)

        message = "Service %s registered" % service.name
        return_dict = [{'status': 'ok',
                       'msg': message,
                       'service_id': service.pk,
                       'service_name': service.name,
                       'service_title': service.title,
                       'available_layers': available_resources
        }]
        return HttpResponse(json.dumps(return_dict),
                            mimetype='application/json',
                            status=200)
    elif type == 'WFS':
        return HttpResponse('Not Implemented (Yet)', status=501)
    elif type == 'WCS':
        return HttpResponse('Not Implemented (Yet)', status=501)
    else:
        return HttpResponse(
            'Invalid Method / Type combo: ' + 
            'Only Indexed WMS, WFS and WCS supported',
            mimetype="text/plain",
            status=400)

def _register_indexed_layers(service, wms=None, verbosity=False):
    """
    Register layers for an indexed service (only WMS/OWS currently supported
    """
    logger.info("Registering layers for %s" % service.base_url)
    if re.match("WMS|OWS", service.type):
        wms = wms or WebMapService(service.base_url)
        count = 0
        for layer in list(wms.contents):
            wms_layer = wms[layer]
            logger.info("Registering layer %s" % wms_layer.name)
            if verbosity:
                print "Importing layer %s" % layer
            layer_uuid = str(uuid.uuid1())
            if not wms_layer.keywords:
                keywords = []
            else:
                keywords = map(lambda x: x[:100], wms_layer.keywords)
            if not wms_layer.abstract:
                abstract = ""
            else:
                abstract = wms_layer.abstract

            srs = None
            if 'EPSG:900913' in wms_layer.crsOptions:
                srs = 'EPSG:900913'
            elif len(wms_layer.crsOptions) > 0:
                matches = re.findall('EPSG\:(3857|102100|102113)', ' '.join(wms_layer.crsOptions))
                if matches:
                    srs = matches[0]
            if srs is None:
                message = "%d Incompatible projection - try setting the service as cascaded" % count
                return_dict = {'status': 'ok', 'msg': message }
                return HttpResponse(json.dumps(return_dict),
                                mimetype='application/json',
                                status=200)

            llbbox = list(wms_layer.boundingBoxWGS84)
            bbox = llbbox_to_mercator(llbbox)

            # Need to check if layer already exists??
            llbbox = list(wms_layer.boundingBoxWGS84)
            saved_layer, created = Layer.objects.get_or_create(
                service=service,
                typename=wms_layer.name,
                defaults=dict(
                    name=wms_layer.name,
                    store=service.name, #??
                    storeType="remoteStore",
                    workspace="remoteWorkspace",
                    title=wms_layer.title,
                    abstract=abstract,
                    uuid=layer_uuid,
                    owner=None,
                    srs=srs,
                    bbox = bbox,
                    llbbox = llbbox,
                    geographic_bounding_box=bbox_to_wkt(str(llbbox[0]), str(llbbox[1]),
                                                        str(llbbox[2]), str(llbbox[3]), srid="EPSG:4326")
                )
            )
            if created:
                saved_layer.save()
                saved_layer.set_default_permissions()
                saved_layer.keywords.add(*keywords)
                saved_layer.set_layer_attributes()
                saved_layer.save_to_geonetwork()

                service_layer, created = ServiceLayer.objects.get_or_create(
                    service=service,
                    typename=wms_layer.name
                )
                service_layer.layer = saved_layer
                service_layer.title=wms_layer.title,
                service_layer.description=wms_layer.abstract,
                service_layer.styles=wms_layer.styles
                service_layer.save()
            count += 1
        message = "%d Layers Registered" % count
        return_dict = {'status': 'ok', 'msg': message }
        return HttpResponse(json.dumps(return_dict),
                            mimetype='application/json',
                            status=200)
    elif service.type == 'WFS':
        return HttpResponse('Not Implemented (Yet)', status=501)
    elif service.type == 'WCS':
        return HttpResponse('Not Implemented (Yet)', status=501)
    else:
        return HttpResponse('Invalid Service Type', status=400)

def _register_harvested_service(type, url, name, username, password, owner=None):
    """
    Register a CSW or OGP service  - stub only.  Needs to iterate through all layers and register
    the layers and the services they originate from.
    """
    if type == 'CSW':
        # Make this CSW Agnostic (i.e. Not GeoNetwork specific)
        gn = Layer.objects.gn_catalog
        id, service_uuid = gn.add_harvesting_task('CSW', name, url) 
        service = Service(type = type,
                            method='H',
                            base_url = url,
                            name = name,
                            owner=owner,
                            uuid = service_uuid,
                            external_id = id)
        service.save()
        message = "Service %s registered" % service.name
        return_dict = {'status': 'ok', 'msg': message,
                        'id': service.pk,
                        'available_layers': []}
        return HttpResponse(json.dumps(return_dict),
                            mimetype='application/json',
                            status=200)
    elif type== "OGP":
        harvest_ogp_service(name,url)
    else:
        return HttpResponse(
            'Invalid Method / Type combo: ' + 
            'Only Harvested CSW supported',
            mimetype="text/plain",
            status=400
        )

def _register_arcgis_url(url,username, password, owner=None):
    """
    Register an ArcGIS REST service URL
    """
    #http://maps1.arcgisonline.com/ArcGIS/rest/services

    baseurl = _clean_url(url)
    if re.search("\/MapServer\/*(f=json)*", baseurl):
        #This is a MapService
        arcserver = ArcMapService(baseurl)
        return_json = [_process_arcgis_service(arcserver, owner)]

    else:
        #This is a Folder
        arcserver = ArcFolder(baseurl)
        return_json = _process_arcgis_folder(arcserver, services=[], owner=owner)

    return HttpResponse(json.dumps(return_json),
                        mimetype='application/json',
                        status=200)

def _register_arcgis_layers(service, arc=None, verbosity=False):
    """
    Register layers from an ArcGIS REST service
    """
    arc = arc or ArcMapService(service.base_url)
    for layer in arc.layers:
        count = 0
        layer_uuid = str(uuid.uuid1())
        layer_bbox = [layer.extent.xmin, layer.extent.ymin, layer.extent.xmax, layer.extent.ymax]
        llbbox =  mercator_to_llbbox(layer_bbox)
        # Need to check if layer already exists??
        saved_layer, created = Layer.objects.get_or_create(
            service=service,
            typename=layer.id,
            defaults=dict(
                name=layer.id,
                store=service.name, #??
                storeType="remoteStore",
                workspace="remoteWorkspace",
                title=layer.name,
                abstract=layer._json_struct['description'],
                uuid=layer_uuid,
                owner=None,
                srs="EPSG:%s" % layer.extent.spatialReference.wkid,
                bbox = layer_bbox,
                llbbox = llbbox,
                geographic_bounding_box=bbox_to_wkt(str(llbbox[0]), str(llbbox[1]),
                                                    str(llbbox[2]), str(llbbox[3]), srid="EPSG:4326" )
            )
        )
        if created:
            saved_layer.set_default_permissions()
            saved_layer.save()
            saved_layer.save_to_geonetwork()

            service_layer, created = ServiceLayer.objects.get_or_create(
                service=service,
                typename=layer.id
            )
            service_layer.layer = saved_layer
            service_layer.title=layer.name,
            service_layer.description=saved_layer.abstract,
            service_layer.styles=None
            service_layer.save()
        count += 1
    message = "%d Layers Registered" % count
    return_dict = {'status': 'ok', 'msg': message }
    return HttpResponse(json.dumps(return_dict),
                        mimetype='application/json',
                        status=200)

def _process_arcgis_folder(folder, services=[], owner=None):
    """
    Iterate through folders and services in an ArcGIS REST service folder
    """
    for service in folder.services:
        if  isinstance(service,ArcMapService) and service.spatialReference.wkid in [102100,3857,900913]:
            print "Base URL is %s" % service.url
            result_json = _process_arcgis_service(service, owner)
            services.append(result_json)
        else:
            return_dict = {}
            return_dict['msg'] =  _("Could not find any layers in a compatible projection:") + service.url
            services.append(return_dict)
    for subfolder in folder.folders:
        _process_arcgis_folder(subfolder, services, owner)
    return services

def _process_arcgis_service(arcserver, owner):
    """
    Create a Service model instance for an ArcGIS REST service
    """
    arc_url = _clean_url(arcserver.url)
    try:
        service = Service.objects.get(base_url=arc_url)
        return_dict = {}
        return_dict['service_id'] = service.pk
        return_dict['msg'] = "This is an existing Service"
        return service.base_url
    except:
        pass

        service, created = Service.objects.get_or_create(base_url = arc_url)
        if created:
            service.type = 'REST'
            service.method='I'
            service.name = _get_valid_name(arcserver.mapName)
            service.title = arcserver.mapName
            service.abstract = arcserver.serviceDescription
            service.online_resource = arc_url
            service.owner=owner
            service.save()

            available_resources = []
            for layer in list(arcserver.layers):
                available_resources.append([layer.id, layer.name])

        if settings.USE_QUEUE:
            #Create a layer import job
            WebServiceHarvestLayersJob.objects.get_or_create(service=service)
        else:
            _register_arcgis_layers(service, arc=arcserver)

        message = "Service %s registered" % service.name
        return_dict = {'status': 'ok',
                       'msg': message,
                       'service_id': service.pk,
                       'service_name': service.name,
                       'service_title': service.title,
                       'available_layers': available_resources
        }
        return return_dict



def harvest_ogp_service(url, num_rows=100, start=0,owner=None):
    base_query_str =  "?q=_val_:%22sum(sum(product(9.0,map(sum(map(MinX,-180.0,180,1,0)," +  \
        "map(MaxX,-180.0,180.0,1,0),map(MinY,-90.0,90.0,1,0),map(MaxY,-90.0,90.0,1,0)),4,4,1,0))),0,0)%22" + \
        "&debugQuery=false&&fq={!frange+l%3D1+u%3D10}product(2.0,map(sum(map(sub(abs(sub(0,CenterX))," + \
        "sum(171.03515625,HalfWidth)),0,400000,1,0),map(sub(abs(sub(0,CenterY)),sum(75.84516854027,HalfHeight))," + \
        "0,400000,1,0)),0,0,1,0))&wt=json&fl=Name,CollectionId,Institution,Access,DataType,Availability," + \
        "LayerDisplayName,Publisher,GeoReferenced,Originator,Location,MinX,MaxX,MinY,MaxY,ContentDate,LayerId," + \
        "score,WorkspaceName,SrsProjectionCode&sort=score+desc&fq=DataType%3APoint+OR+DataType%3ALine+OR+" + \
        "DataType%3APolygon+OR+DataType%3ARaster+OR+DataType%3APaper+Map&fq=Access:Public"

    #base_query_str += "&fq=Institution%3AHarvard"

    fullurl = url + base_query_str + ("&rows=%d&start=%d" % (num_rows, start))
    response = urllib.urlopen(fullurl).read()
    json_response = json.loads(response)
    result_count =  json_response["response"]["numFound"]
    process_ogp_results(json_response)

    while start < result_count:
        start = start + num_rows
        harvest_ogp_service(url, num_rows, start)

def process_ogp_results(result_json, owner=None):
    for doc in result_json["response"]["docs"]:
        try:
            locations = json.loads(doc["Location"])
        except:
            continue
        if "tilecache" in locations:
            service_url = locations["tilecache"][0]
            service_type = "WMS"
        elif "wms" in locations:
            service_url = locations["wms"][0]
            if "wfs" in locations:
                service_type = "OWS"
            else:
                service_type = "WMS"
        else:
            pass

        #Harvard is a special case
        if doc["Institution"] == "Harvard":
            service_type = "HGL"

        service = None
        try:
            service = Service.objects.get(base_url=service_url)
        except Service.DoesNotExist:
            if service_type in ["WMS","OWS", "HGL"]:
                try:
                    response = _process_wms_service(service_url, service_type, None, None)
                    r_json = json.loads(response.content)
                    service = Service.objects.get(id=r_json[0]["service_id"])
                except Exception, e:
                    print str(e)

        if service:
                typename = doc["Name"]
                if service_type == "HGL":
                    typename = typename.replace("SDE.","")
                elif doc["WorkspaceName"]:
                    typename = doc["WorkspaceName"] + ":" + typename


                bbox = (
                    float(doc['MinX']),
                    float(doc['MinY']),
                    float(doc['MaxX']),
                    float(doc['MaxY']),
                )

                layer_uuid = str(uuid.uuid1())
                saved_layer, created = Layer.objects.get_or_create(service=service, typename=typename,
                    defaults=dict(
                    name=doc["Name"],
                    service = service,
                    uuid=layer_uuid,
                    store=service.name, #??
                    storeType="remoteStore",
                    workspace=doc["WorkspaceName"],
                    title=doc["LayerDisplayName"],
                    owner=None,
                    srs="EPSG:900913", #Assumption
                    bbox = llbbox_to_mercator(list(bbox)),
                    llbbox = list(bbox),
                    geographic_bounding_box=bbox_to_wkt(str(bbox[0]), str(bbox[1]),
                                                        str(bbox[2]), str(bbox[3]), srid="EPSG:4326" )
                    )
                )
                saved_layer.set_default_permissions()
                saved_layer.save()
                saved_layer.save_to_geonetwork()
                service_layer, created = ServiceLayer.objects.get_or_create(service=service,typename=typename,
                                                                            defaults=dict(
                                                                                title=doc["LayerDisplayName"]
                                                                            )
                )
                if service_layer.layer is None:
                    service_layer.layer = saved_layer
                    service_layer.save()

def service_detail(request, service_id):
    '''
    This view shows the details of a service 
    '''
    service = get_object_or_404(Service,pk=service_id)
    layers = Layer.objects.filter(service=service) 
    return render_to_response("services/service_detail.html", RequestContext(request, {
        'service': service,
        'layers': layers,
        'permissions_json': json.dumps(_perms_info(service, SERVICE_LEV_NAMES))
    }))

@login_required
def edit_service(request, service_id):
    """
    Edit an existing Service
    """
    service_obj = get_object_or_404(Service,pk=service_id)


    if request.method == "POST":
        service_form = ServiceForm(request.POST, instance=service_obj, prefix="service")
        if service_form.is_valid():
            service_obj = service_form.save(commit=False)
            service_obj.keywords.clear()
            service_obj.keywords.add(*service_form.cleaned_data['keywords'])
            service_obj.save()

            return HttpResponseRedirect(service_obj.get_absolute_url())
    else:
        service_form = ServiceForm(instance=service_obj, prefix="service")


    return render_to_response("services/service_edit.html", RequestContext(request, {
                "service": service_obj,
                "service_form": service_form
            }))

def update_layers(service):
    """
    Import/update layers for an existing service
    """
    if service.method == "C":
        _register_cascaded_layers(service, None, owner=service.owner)
    elif service.type in ["WMS","OWS"]:
        _register_indexed_layers(service)
    elif service.type in ["REST"]:
        _register_arcgis_layers(service, None)

@login_required
def remove_service(request, service_id):
    '''
    Delete a service, and its constituent layers. 
    '''
    service_obj = get_object_or_404(Service,pk=service_id)

    if not request.user.has_perm('maps.delete_service', obj=service_obj):
        return HttpResponse(loader.render_to_string('401.html', 
            RequestContext(request, {'error_message': 
                _("You are not permitted to remove this service.")})), status=401)

    if request.method == 'GET':
        return render_to_response("services/service_remove.html", RequestContext(request, {
            "service": service_obj
        }))
    elif request.method == 'POST':
        servicelayers = service_obj.servicelayer_set.all()
        for servicelayer in servicelayers:
            servicelayer.delete()

        layers = service_obj.layer_set.all()
        for layer in layers:
            layer.delete()
        service_obj.delete()

        return HttpResponseRedirect(reverse("services"))

def set_service_permissions(service, perm_spec):
    if "authenticated" in perm_spec:
        service.set_gen_level(AUTHENTICATED_USERS, perm_spec['authenticated'])
    if "anonymous" in perm_spec:
        service.set_gen_level(ANONYMOUS_USERS, perm_spec['anonymous'])
    users = [n for (n, p) in perm_spec['users']]
    service.get_user_levels().exclude(user__username__in = users + [service.owner]).delete()
    for username, level in perm_spec['users']:
        user = User.objects.get(username=username)
        service.set_user_level(user, level)

@login_required
def ajax_service_permissions(request, service_id):
    service = get_object_or_404(Service,pk=service_id) 
    if not request.user.has_perm("maps.change_service_permissions", obj=service):
        return HttpResponse(
            'You are not allowed to change permissions for this service',
            status=401,
            mimetype='text/plain'
        )

    if not request.method == 'POST':
        return HttpResponse(
            'You must use POST for editing service permissions',
            status=405,
            mimetype='text/plain'
        )

    spec = json.loads(request.raw_post_data)
    set_service_permissions(service, spec)

    return HttpResponse(
        "Permissions updated",
        status=200,
        mimetype='text/plain')

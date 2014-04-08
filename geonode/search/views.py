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
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
import json
import logging
from geonode.flexidates import parse_julian_date
from geonode.maps.models import Map
from geonode.maps.views import default_map_config


logger = logging.getLogger(__name__)


# Haystack Implementation


import xmlrpclib
from haystack.inputs import AutoQuery, Raw
from haystack.query import SearchQuerySet, SQ



default_facets = ["map", "layer", "vector", "raster", "contact", "keywords", "service"]
fieldsets = {
    "brief": ["name", "type", "description"],
    "summary": ["name", "type", "description", "owner"],
    "full": ["name", "type", "description", "owner", "language"],
}


def search(request):
    """
    View that drives the search page
    """

    DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config()
    #DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config(request)
    # for non-ajax requests, render a generic search page

    params = dict(request.REQUEST)

    map = Map(projection="EPSG:900913", zoom=1, center_x=0, center_y=0)

    # Default Counts to 0, JS will Load the Correct Counts
    facets = {}
    for facet in default_facets:
        facets[facet] = 0

    return render_to_response("search/search.html", RequestContext(request, {
        "init_search": json.dumps(params),
        #'viewer_config': json.dumps(map.viewer_json(added_layers=DEFAULT_BASE_LAYERS, authenticated=request.user.is_authenticated())),
        "viewer_config": json.dumps(map.viewer_json(*DEFAULT_BASE_LAYERS)),
        "GOOGLE_API_KEY": settings.GOOGLE_API_KEY,
        "site": settings.SITEURL,
        "facets": None,
        "keywords": None
    }))


def haystack_search_api(request):
    """
    View that drives the search api
    """

    # Retrieve Query Params
    id = request.REQUEST.get("id", None)
    query = request.REQUEST.get('q',None)
    name = request.REQUEST.get("name", None)
    category = request.REQUEST.get("cat", None)
    limit = int(request.REQUEST.get("limit", getattr(settings, "HAYSTACK_SEARCH_RESULTS_PER_PAGE", 20)))
    startIndex = int(request.REQUEST.get("startIndex", 0))
    startPage = int(request.REQUEST.get("startPage", 0))
    sort = request.REQUEST.get("sort", "relevance")
    order = request.REQUEST.get("order", "asc")
    type = request.REQUEST.get("type", None)
    fields = request.REQUEST.get("fields", None)
    fieldset = request.REQUEST.get("fieldset", None)
    format = request.REQUEST.get("format", "json")
    temporal_start = request.REQUEST.get("temporalStart", None)
    temporal_end = request.REQUEST.get("temporalEnd", None)
    keyword = request.REQUEST.get("keyword", None)
    service = request.REQUEST.get("service", None)
    local = request.REQUEST.get("local", None)

    # Geospatial Elements
    bbox = request.REQUEST.get("bbox", None)

    sqs = SearchQuerySet()

    limit = min(limit,500)

    # Filter by ID
    if id:
        sqs = sqs.narrow("django_id:%s" % id)

    # Filter by Type
    if type is not None:
        if type in ["map", "layer", "contact"]:
            # Type is one of our Major Types (not a sub type)
            sqs = sqs.narrow("type:%s" % type)
        elif type in ["vector", "raster"]:
            # Type is one of our sub types
            sqs = sqs.narrow("subtype:%s" % type)

    # Filter by Query Params
    if query:
        if query.startswith("\"") and query.endswith("\""):
            sqs = sqs.filter(content_exact=Raw(query.replace("\"","")))
        else:
            words = query.split()
            for word in range(0,len(words)-1):
                if word == 0:
                    sqs = sqs.filter(content=Raw(words[word]))
                elif words[word] in ["AND","OR"]:
                    pass
                elif words[word-1] == "OR":
                    sqs = sqs.filter_or(content=Raw(words[word]))
                else:
                    sqs = sqs.filter(content=Raw(words[word]))


        for word in query.split("AND"):
            sqs = sqs.filter(content=Raw(word))
        for word in query.split("OR"):
            sqs = sqs.filter_or(content=Raw(word))

    # filter by cateory
    if category is not None:
        sqs = sqs.narrow('category:%s' % category)

    #filter by keyword
    if keyword is not None:
        sqs = sqs.narrow('keywords:%s' % keyword)

    #filter by service
    if service is not None:
        sqs = sqs.narrow('service:%s' % service)

    if local is not None:
        sqs = sqs.narrow('local:%s' % local)

    # Apply Sort
    # TODO: Handle for Revised sort types
    # [relevance, alphabetically, rating, created, updated, popularity]
    if sort.lower() == "newest":
        sqs = sqs.order_by("-date")
    elif sort.lower() == "oldest":
        sqs = sqs.order_by("date")
    elif sort.lower() == "alphaaz":
        sqs = sqs.order_by("title")
    elif sort.lower() == "alphaza":
        sqs = sqs.order_by("-title")

    # Setup Search Results
    results = []

    if temporal_start:
        temporal_start = parse_julian_date(temporal_start)
    if temporal_end:
        temporal_end = parse_julian_date(temporal_end)


    if temporal_start and temporal_end:
        #Return anything with a start date < temporal_end or an end date > temporal_start
        sqs = sqs.filter(
            SQ(temporal_extent_end_julian__gte=temporal_start) & SQ(temporal_extent_start_julian__lte=temporal_end)
        )
    elif temporal_start:
        #Return anything with an end date < temporal_start or (any start date and no end date)
        sqs = sqs.filter(
            SQ(temporal_extent_end_julian__gte=temporal_start)   |
            SQ(temporal_extent_start__isnull=False) & SQ(temporal_extent_end__isnull=True)
        )
    elif temporal_end:
        #Return anything with a start date < temporal_end or (no start date and any end date)
        sqs = sqs.filter(
            SQ(temporal_extent_start_julian__lte=temporal_end) |
            SQ(temporal_extent_end__isnull=False) & SQ(temporal_extent_start__isnull=True)
        )


    if bbox is not None:
        left,bottom,right,top = bbox.split(',')
        sqs = sqs.filter(
            # first check if the bbox has at least one point inside the window
            SQ(bbox_left__gte=left) & SQ(bbox_left__lte=right) & SQ(bbox_top__gte=bottom) & SQ(bbox_top__lte=top) | #check top_left is inside the window
            SQ(bbox_right__lte=right) &  SQ(bbox_right__gte=left) & SQ(bbox_top__lte=top) &  SQ(bbox_top__gte=bottom) | #check top_right is inside the window
            SQ(bbox_bottom__gte=bottom) & SQ(bbox_bottom__lte=top) & SQ(bbox_right__lte=right) &  SQ(bbox_right__gte=left) | #check bottom_right is inside the window
            SQ(bbox_top__lte=top) & SQ(bbox_top__gte=bottom) & SQ(bbox_left__gte=left) & SQ(bbox_left__lte=right) | #check bottom_left is inside the window
            # then check if the bbox is including the window
            SQ(bbox_left__lte=left) & SQ(bbox_right__gte=right) & SQ(bbox_bottom__lte=bottom) & SQ(bbox_top__gte=top)
        )


    # Filter by permissions
    """
    for i, result in enumerate(sqs):
        if result.type == 'layer':
            if not request.user.has_perm('maps.view_layer',obj = result.object):
                sqs = sqs.exclude(id = result.id)
        if result.type == 'map':
            if not request.user.has_perm('maps.view_map',obj = result.object):
                sqs = sqs.exclude(id = result.id)
    """

    # Build the result based on the limit
    for i, result in enumerate(sqs[startIndex:startIndex + limit]):
        logger.info(result)
        data = result.get_stored_fields()
        # data.pop("modified",None)
        # data.pop("created",None)
        data["modified"] = data["modified"].strftime("%Y-%m-%dT%H:%M:%S.%f")
        data["created"] = data["created"].strftime("%Y-%m-%dT%H:%M:%S.%f")
        #data.pop("json",None)
        data["iid"] =  i + startIndex
        print (data)
        #data.update({"iid": i + startIndex})
        results.append(data)



    # Filter Fields/Fieldsets
    if fieldset:
        if fieldset in fieldsets.keys():
            for result in results:
                for key in result.keys():
                    if key not in fieldsets[fieldset]:
                        del result[key]
    elif fields:
        fields = fields.split(',')
        for result in results:
            for key in result.keys():
                if key not in fields:
                    del result[key]

    # Setup Facet Counts
    sqs = sqs.facet("type").facet("subtype")

    sqs = sqs.facet('category')

    sqs = sqs.facet('keywords')

    sqs = sqs.facet('service')

    sqs = sqs.facet('local')

    facets = sqs.facet_counts()

    # Prepare Search Results
    from django.core.serializers.json import DjangoJSONEncoder
    #results =  json.dumps(results, cls=DjangoJSONEncoder).replace("\\","")

    data = {
        "success": True,
        "total": sqs.count(),
        "query_info": {
            "q": query,
            "startIndex": startIndex,
            "limit": limit,
            "sort": sort,
            "type": type,
        },
        "facets": facets,
        "results": results,
        "counts": dict(facets.get("fields")['type']+facets.get('fields')['subtype']) if sqs.count() > 0 else [],
        "categories": [facet[0] for facet in facets.get('fields')['category']] if sqs.count() > 0 else [],
        "keywords": [facet[0] for facet in facets.get('fields')['keywords']] if sqs.count() > 0 else [],
        "services": [facet[0] for facet in facets.get('fields')['service']] if sqs.count() > 0 else [],
        "local":  [facet[0] for facet in facets.get('fields')['local']] if sqs.count() > 0 else []
    }

    # Return Results
    if format:
        if format == "xml":
            return HttpResponse(xmlrpclib.dumps((data,), allow_none=True), mimetype="text/xml")
        elif format == "json":
            return HttpResponse(json.dumps(data), mimetype="application/json")
    else:
        return HttpResponse(json.dumps(data), mimetype="application/json")


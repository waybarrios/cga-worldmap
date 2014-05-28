# Create your views here.
import logging
import re
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, loader
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.utils.html import escape
from geonode.people.forms import ProfileForm
from geonode.utils import ogc_server_settings
from geonode.base.enumerations import CHARSETS
from geonode.base.models import TopicCategory
from geonode.maps.models import Map, MapLayer
from geonode.layers.models import Layer, Attribute
from geonode.layers.views import layer_upload as geonode_upload
from geonode.worldmap.gazetteer.utils import update_gazetteer, queue_gazetteer_update
from geonode.worldmap.profile.forms import ContactProfileForm
from geonode.worldmap.layers.forms import LayerCreateForm, LayerCategoryForm, GEOMETRY_CHOICES, GazetteerAttributeForm
from geonode.worldmap.stats.models import LayerStats
from geonode.geoserver.helpers import get_sld_for
from django.utils import simplejson as json
from geonode.layers.views import _resolve_layer, _PERMISSION_MSG_METADATA
from django.forms.models import inlineformset_factory
from geonode.worldmap.layers.forms import WorldMapLayerForm
from geonode.encode import XssCleaner, despam
from django.core.cache import cache
from geonode.upload.models import Upload
from geonode.worldmap.gazetteer.forms import GazetteerForm

logger = logging.getLogger("geonode.worldmap.maps.views")

_ASYNC_UPLOAD = ogc_server_settings.DATASTORE == True

def addLayerJSON(request):
    logger.debug("Enter addLayerJSON")
    layername = request.POST.get('layername', False)
    logger.debug("layername is [%s]", layername)

    if layername:
        try:
            layer = Layer.objects.get(typename=layername)
            if not request.user.has_perm("maps.view_layer", obj=layer):
                return HttpResponse(status=401)
            sfJSON = {'layer': layer.layer_config(request.user)}
            logger.debug('sfJSON is [%s]', str(sfJSON))
            return HttpResponse(json.dumps(sfJSON))
        except Exception, e:
            logger.debug("Could not find matching layer: [%s]", str(e))
            return HttpResponse(str(e), status=500)

    else:
        return HttpResponse(status=500)


def ajax_layer_edit_check(request, layername):
    layer = get_object_or_404(Layer, typename=layername);
    editable = request.user.has_perm("maps.change_layer", obj=layer)
    return HttpResponse(
        str(editable),
        status=200 if editable else 403,
        mimetype='text/plain'
    )

def ajax_layer_update(request, layername):
    layer = get_object_or_404(Layer, typename=layername)
    if settings.USE_QUEUE:
        layer.queue_bounds_update()
        if settings.USE_GAZETTEER:
            layer.queue_gazetteer_update()
    else:
        layer.update_bounds()
        if settings.USE_GAZETTEER:
            layer.update_gazetteer()

    return HttpResponse(
        "Layer updated",
        status=200,
        mimetype='text/plain'
    )

def ajax_layer_permissions(request, layername, use_email=False):
    layer = get_object_or_404(Layer, typename=layername)

    if not request.method == 'POST':
        return HttpResponse(
            'You must use POST for editing layer permissions',
            status=405,
            mimetype='text/plain'
        )

    if not request.user.has_perm("maps.change_layer_permissions", obj=layer):
        return HttpResponse(
            'You are not allowed to change permissions for this layer',
            status=401,
            mimetype='text/plain'
        )

    permission_spec = json.loads(request.raw_post_data)
    layer.set_permissions(permission_spec, use_email)

    return HttpResponse(
        "Permissions updated",
        status=200,
        mimetype='text/plain'
    )

def ajax_layer_permissions_by_email(request, layername):
    return ajax_layer_permissions(request, layername, True)

def ajax_increment_layer_stats(request):
    if request.method != 'POST':
        return HttpResponse(
            content='ajax user lookup requires HTTP POST',
            status=405,
            mimetype='text/plain'
        )
    if request.POST['layername'] != '':
        layer_match = Layer.objects.filter(typename=request.POST['layername'])[:1]
        for l in layer_match:
            layerStats,created = LayerStats.objects.get_or_create(layer=l)
            layerStats.visits += 1
            first_visit = True
            if request.session.get('visitlayer' + str(l.id), False):
                first_visit = False
            else:
                request.session['visitlayer' + str(l.id)] = True
            if first_visit or created:
                layerStats.uniques += 1
            layerStats.save()

    return HttpResponse(
        status=200
    )


@login_required
def create_pg_layer(request):
    if request.method == 'GET':
        layer_form = LayerCreateForm(prefix="layer")

        # Determine if this page will be shown in a tabbed panel or full page
        pagetorender = "layers/layer_create_tab.html" if "tab" in request.GET else "layers/layer_create.html"


        return render_to_response(pagetorender, RequestContext(request, {
            "layer_form": layer_form,
            "customGroup": settings.CUSTOM_AUTH["name"] if settings.CUSTOM_AUTH["enabled"] else '',
            "geoms": GEOMETRY_CHOICES
        }))

    if request.method == 'POST':
        from geonode.layers.utils import create_django_record, get_valid_layer_name
        from ordereddict import OrderedDict
        layer_form = LayerCreateForm(request.POST)
        if layer_form.is_valid():
            cat = Layer.objects.gs_catalog

            # Assume default workspace
            ws = cat.get_workspace(settings.DEFAULT_WORKSPACE)
            if ws is None:
                msg = 'Specified workspace [%s] not found' % settings.DEFAULT_WORKSPACE
                return HttpResponse(msg, status='400')

            # Assume datastore used for PostGIS
            store = ogc_server_settings.DATASTORE_NAME
            if store is None:
                msg = 'Specified store [%s] not found' % ogc_server_settings.DATASTORE_NAME
                return HttpResponse(msg, status='400')

            #TODO: Let users create their own schema
            attribute_list = [
                ["the_geom","com.vividsolutions.jts.geom." + layer_form.cleaned_data['geom'],{"nillable":False}],
                ["Name","java.lang.String",{"nillable":True}],
                ["Description","java.lang.String", {"nillable":True}],
                ["Start_Date","java.util.Date",{"nillable":True}],
                ["End_Date","java.util.Date",{"nillable":True}],
                ["String_Value_1","java.lang.String",{"nillable":True}],
                ["String_Value_2","java.lang.String", {"nillable":True}],
                ["Number_Value_1","java.lang.Float",{"nillable":True}],
                ["Number_Value_2","java.lang.Float", {"nillable":True}],
                ]

            # Add geometry to attributes dictionary, based on user input; use OrderedDict to remember order
            #attribute_list.insert(0,[u"the_geom",u"com.vividsolutions.jts.geom." + layer_form.cleaned_data['geom'],{"nillable":False}])

            name = get_valid_layer_name(layer_form.cleaned_data['name'])
            permissions = layer_form.cleaned_data["permissions"]

            try:
                logger.info("Create layer %s", name)
                layer = cat.create_native_layer(settings.DEFAULT_WORKSPACE,
                                                ogc_server_settings.DATASTORE_NAME,
                                                name,
                                                name,
                                                escape(layer_form.cleaned_data['title']),
                                                layer_form.cleaned_data['srs'],
                                                attribute_list)

                logger.info("Create default style")
                publishing = cat.get_layer(name)
                sld = get_sld_for(publishing)
                cat.create_style(name, sld)
                publishing.default_style = cat.get_style(name)
                cat.save(publishing)


                logger.info("Create django record")
                geonodeLayer = create_django_record(request.user, layer_form.cleaned_data['title'], layer_form.cleaned_data['keywords'].strip().split(" "), layer_form.cleaned_data['abstract'], layer, permissions)


                redirect_to  = reverse('data_metadata', args=[geonodeLayer.typename])
                if 'mapid' in request.POST and request.POST['mapid'] == 'tab': #if mapid = tab then open metadata form in tabbed panel
                    redirect_to+= "?tab=worldmap_create_panel"
                elif 'mapid' in request.POST and request.POST['mapid'] != '': #if mapid = number then add to parameters and open in full page
                    redirect_to += "?map=" + request.POST['mapid']
                return HttpResponse(json.dumps({
                    "success": True,
                    "redirect_to": redirect_to}))
            except Exception, e:
                logger.exception("Unexpected error.")
                return HttpResponse(json.dumps({
                    "success": False,
                    "errors": ["Unexpected error: " + escape(str(e))]}))

        else:
            #The form has errors, what are they?
            return HttpResponse(layer_form.errors, status='500')

@login_required
def layer_contacts(request, layername):
    layer = get_object_or_404(Layer, typename=layername)
    if request.user.is_authenticated():
        if not request.user.has_perm('layers.change_layer', obj=layer):
            return HttpResponse(loader.render_to_string('401.html',
                                                        RequestContext(request, {'error_message':
                                                                                     _("You are not permitted to modify this layer's metadata")})), status=401)


    poc = layer.poc
    metadata_author = layer.metadata_author

    if request.method == "GET":
        contact_form = ContactProfileForm(prefix="layer")
        if poc.user is None:
            poc_form = ContactProfileForm(instance=poc, prefix="poc")
        else:
            contact_form.fields['poc'].initial = poc.id
            poc_form = ContactProfileForm(prefix="poc")
            poc_form.hidden=True

        if metadata_author.user is None:
            author_form = ContactProfileForm(instance=metadata_author, prefix="author")
        else:
            contact_form.fields['metadata_author'].initial = metadata_author.id
            author_form = ContactProfileForm(prefix="author")
            author_form.hidden=True
    elif request.method == "POST":
        contact_form = ContactProfileForm(request.POST, prefix="layer")
        if contact_form.is_valid():
            new_poc = contact_form.cleaned_data['poc']
            new_author = contact_form.cleaned_data['metadata_author']
            if new_poc is None:
                poc_form = ContactProfileForm(request.POST, prefix="poc")
                if poc_form.has_changed and poc_form.is_valid():
                    new_poc = poc_form.save()
            else:
                poc_form = ContactProfileForm(prefix="poc")
                poc_form.hidden=True

            if new_author is None:
                author_form = ContactProfileForm(request.POST, prefix="author")
                if author_form.has_changed and author_form.is_valid():
                    new_author = author_form.save()
            else:
                author_form = ContactProfileForm(prefix="author")
                author_form.hidden=True

            if new_poc is not None and new_author is not None:
                layer.poc = new_poc
                layer.metadata_author = new_author
                layer.save()
                return HttpResponseRedirect("/layers/" + layer.typename)



    #Deal with a form submission via ajax
    if request.method == 'POST' and (not contact_form.is_valid()):
        data = render_to_response("layers/layer_contacts.html", RequestContext(request, {
            "layer": layer,
            "contact_form": contact_form,
            "poc_form": poc_form,
            "author_form": author_form,
            "lastmap" : request.session.get("lastmap"),
            "lastmapTitle" : request.session.get("lastmapTitle")
        }))
        return HttpResponse(data, status=412)

    #Display the view on a regular page
    return render_to_response("maps/layer_contacts.html", RequestContext(request, {
        "layer": layer,
        "contact_form": contact_form,
        "poc_form": poc_form,
        "author_form": author_form,
        "lastmap" : request.session.get("lastmap"),
        "lastmapTitle" : request.session.get("lastmapTitle")
    }))

def category_list():
    topics = TopicCategory.objects.all()
    topicArray = []
    for topic in topics:
        topicArray.append([topic.slug, topic.name])
    return topicArray


@login_required
def layer_metadata(request, layername, template='layers/layer_metadata.html'):
    layer = _resolve_layer(request, layername, 'layers.change_layer', _PERMISSION_MSG_METADATA)
    layer_attribute_set = inlineformset_factory(Layer, Attribute, extra=0, form=GazetteerAttributeForm, )

    topic_category = layer.category
    poc = layer.poc
    metadata_author = layer.metadata_author
    gazetteer_form = None

    ######## GAZETTEER SETUP #########
    startAttributeQuerySet = Attribute.objects.filter(layer=layer).filter(is_gaz_start_date=True)
    endAttributeQuerySet = Attribute.objects.filter(layer=layer).filter(is_gaz_end_date=True)
    fieldTypes = {}
    attributeOptions = layer.attribute_set.filter(
        attribute_type__in=['xsd:dateTime', 'xsd:date', 'xsd:int', 'xsd:string', 'xsd:bigint', 'xsd:double'])
    for option in attributeOptions:
        try:
            fieldTypes[option.id] = option.attribute_type
        except Exception, e:
            logger.info("Could not get type for %s", option)
    show_gazetteer_form = request.user.is_superuser and layer.store == ogc_server_settings.server['DATASTORE'] and settings.USE_GAZETTEER
    attribute_errors = None
    ######## END GAZETTEER SETUP #########

    if request.method == "POST":
        layer_form = WorldMapLayerForm(request.POST, instance=layer, prefix="resource")
        attribute_form = layer_attribute_set(request.POST, instance=layer, prefix="layer_attribute_set", queryset=Attribute.objects.order_by('display_order'))
        category_form = LayerCategoryForm(request.POST,prefix="category_choice_field",
            initial=int(request.POST["category_choice_field"]) if "category_choice_field" in request.POST else None)
        if show_gazetteer_form:
            gazetteer_form = GazetteerForm(request.POST)
            gazetteer_form.fields['startDate'].queryset = gazetteer_form.fields['endDate'].queryset = layer.attribute_set
    else:
        layer_form = WorldMapLayerForm(instance=layer, prefix="resource")
        attribute_form = layer_attribute_set(instance=layer, prefix="layer_attribute_set", queryset=Attribute.objects.order_by('display_order'))
        category_form = LayerCategoryForm(prefix="category_choice_field", initial=topic_category.id if topic_category else None)
        if show_gazetteer_form:
            gazetteer_form = GazetteerForm()
            gazetteer_form.fields['project'].initial = layer.gazetteer_project
            gazetteer_form.fields['startDate'].queryset = gazetteer_form.fields['endDate'].queryset = attributeOptions
            if gazetteer_form.fields['startDate'].queryset.count() == 0:
                gazetteer_form.fields['startDate'].empty_label = gazetteer_form.fields['endDate'].empty_label = _(
                'No date fields available')
            if startAttributeQuerySet.exists():
                gazetteer_form.fields['startDate'].initial = startAttributeQuerySet[0].id
                gazetteer_form.fields['startDateFormat'].initial = startAttributeQuerySet[0].date_format
            if endAttributeQuerySet.exists():
                gazetteer_form.fields['endDate'].initial = endAttributeQuerySet[0].id
                gazetteer_form.fields['endDateFormat'].initial = endAttributeQuerySet[0].date_format

    tab = None
    if "tab" in request.GET:
        tab = request.GET["tab"]

    if request.method == "POST" and layer_form.is_valid() and attribute_form.is_valid() and category_form.is_valid():

        new_poc = layer_form.cleaned_data['poc']
        new_author = layer_form.cleaned_data['metadata_author']
        new_keywords = layer_form.cleaned_data['keywords']

        if new_poc is None:
            if poc.user is None:
                poc_form = ProfileForm(request.POST, prefix="poc", instance=poc)
            else:
                poc_form = ProfileForm(request.POST, prefix="poc")
            if poc_form.has_changed and poc_form.is_valid():
                new_poc = poc_form.save()

        if new_author is None:
            if metadata_author.user is None:
                author_form = ProfileForm(request.POST, prefix="author",
                                          instance=metadata_author)
            else:
                author_form = ProfileForm(request.POST, prefix="author")
            if author_form.has_changed and author_form.is_valid():
                new_author = author_form.save()

        new_category = TopicCategory.objects.get(id=category_form.cleaned_data['category_choice_field'])


        if "tab" in request.POST:
            tab = request.POST["tab"]

        for form in attribute_form.cleaned_data:
            la = Attribute.objects.get(id=int(form['id'].id))
            la.description = form["description"]
            la.attribute_label = form["attribute_label"]
            la.visible = form["visible"]
            la.display_order = form["display_order"]
            la.searchable = form["searchable"]

            if show_gazetteer_form and gazetteer_form.is_valid():
                la.in_gazetteer = form["in_gazetteer"]
                la.is_gaz_start_date = (la == gazetteer_form.cleaned_data["startDate"])
                la.is_gaz_end_date = (la == gazetteer_form.cleaned_data["endDate"])
                if la.is_gaz_start_date:
                    la.date_format = gazetteer_form.cleaned_data["startDateFormat"].strip() \
                        if len(gazetteer_form.cleaned_data["startDateFormat"]) > 0 else None
                elif la.is_gaz_end_date:
                    la.date_format = gazetteer_form.cleaned_data["endDateFormat"].strip() \
                        if len(gazetteer_form.cleaned_data["endDateFormat"]) > 0 else None

            la.save()
            cache.delete('layer_searchfields_' + layer.typename)

        if new_poc is not None and new_author is not None:
            the_layer = layer_form.save(commit=False)
            codeCleaner = XssCleaner()
            the_layer.abstract = despam(codeCleaner.strip(layer_form.cleaned_data["abstract"]))
            the_layer.category = new_category
            the_layer.keywords.clear()
            the_layer.keywords.add(*new_keywords)

            if show_gazetteer_form and gazetteer_form.is_valid():
                the_layer.in_gazetteer = "gazetteer_include" in request.POST
                if the_layer.in_gazetteer:
                    the_layer.gazetteer_project = gazetteer_form.cleaned_data["project"]
                    if settings.USE_QUEUE:
                        queue_gazetteer_update(the_layer)
                    else:
                        update_gazetteer(the_layer)
            the_layer.save()

            mapid = layer_form.cleaned_data['map_id']

            if "tab" in request.path:
                return HttpResponse(the_layer.category.gn_description, status=200)
            elif mapid != '' and str(mapid).lower() != 'new':
                logger.debug("adding layer to map [%s]", str(mapid))
                maplayer = MapLayer.objects.create(map=Map.objects.get(id=mapid),
                                           name = layer.typename,
                                           group = layer.category.title if layer.category else 'General',
                                           layer_params = '{"selected":true, "title": "' + layer.title + '"}',
                                           source_params = '{"ptype": "gxp_wmscsource"}',
                                           ows_url = settings.GEOSERVER_BASE_URL + "wms",
                                           visibility = True,
                                           stack_order = MapLayer.objects.filter(id=mapid).count()
                )
                maplayer.save()
                return HttpResponseRedirect("/maps/" + mapid)
            else:
                if str(mapid) == "new":
                    return HttpResponseRedirect("/maps/new?layer" + layer.typename)
                else:
                    return HttpResponseRedirect(reverse('layer_detail', args=(layer.typename,)))


    if poc.user is None:
        poc_form = ProfileForm(instance=poc, prefix="poc")
    else:
        layer_form.fields['poc'].initial = poc.id
        poc_form = ProfileForm(prefix="poc")
        poc_form.hidden=True

    if metadata_author.user is None:
        author_form = ProfileForm(instance=metadata_author, prefix="author")
    else:
        layer_form.fields['metadata_author'].initial = metadata_author.id
        author_form = ProfileForm(prefix="author")
        author_form.hidden=True

    for error in attribute_form.errors:
        if len(error) > 0:
            attribute_errors = attribute_form.errors
            break

    #Deal with a form submission via ajax
    if request.method == 'POST' and (not layer_form.is_valid() or not category_form.is_valid() \
            or not attribute_form.is_valid()) and request.is_ajax():
        data = render_to_response("layers/layer_metadata_tab.html", RequestContext(request, {
        "layer": layer,
        "layer_form": layer_form,
        "attribute_form": attribute_form,
        "category_form" : category_form,
        "gazetteer_form": gazetteer_form,
        "show_gazetteer_options": show_gazetteer_form,
        "lastmap" : request.session.get("lastmap"),
        "lastmapTitle" : request.session.get("lastmapTitle"),
        "tab" : tab,
        "datatypes" : json.dumps(fieldTypes),
        "attribute_errors": attribute_errors
        }))
        return HttpResponse(data, status=412)

    #Display the view in a panel tab
    if tab:
        return render_to_response("layers/layer_metadata_tab.html", RequestContext(request, {
        "layer": layer,
        "layer_form": layer_form,
        "attribute_form": attribute_form,
        "category_form" : category_form,
        "gazetteer_form": gazetteer_form,
        "show_gazetteer_options": show_gazetteer_form,
        "lastmap" : request.session.get("lastmap"),
        "lastmapTitle" : request.session.get("lastmapTitle"),
        "tab" : tab,
        "datatypes" : json.dumps(fieldTypes),
    }))


    return render_to_response(template, RequestContext(request, {
        "layer": layer,
        "layer_form": layer_form,
        "category_form": category_form,
        "attribute_form": attribute_form,
        "gazetteer_form": gazetteer_form,
        "show_gazetteer_options": show_gazetteer_form,
        "poc_form": poc_form,
        "author_form": author_form,
        "lastmap" : request.session.get("lastmap"),
        "lastmapTitle" : request.session.get("lastmapTitle"),
        "datatypes" : json.dumps(fieldTypes),
        "attribute_errors": attribute_errors
    }))


def layer_upload(request, template='upload/layer_upload.html'):
    if request.method == 'GET':
        if 'tab' in request.path:
            return render_to_response('upload/layer_upload_tab.html',
                                      RequestContext(request, {
                                          'async_upload' : _ASYNC_UPLOAD,
                                          'incomplete' : Upload.objects.get_incomplete_uploads(request.user),
                                          'charsets': CHARSETS
                                      }))
        else:
            return render_to_response(template,
                                      RequestContext(request, {
                                          'async_upload' : _ASYNC_UPLOAD,
                                          'incomplete' : Upload.objects.get_incomplete_uploads(request.user),
                                          'charsets': CHARSETS
                                      }))
    elif request.method == 'POST':
        return geonode_upload(request)

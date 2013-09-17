import urllib
from django.utils.safestring import mark_safe
from geonode import settings
from lxml import etree
from django.db import models
from django.db.models import signals
import httplib2
from geonode.layers.models import Attribute, Layer
from django.utils.translation import ugettext_lazy as _

# Create your models here.
# class SearchAttribute(Attribute):
#     #attribute = models.ForeignKey(Attribute, blank=False, null=False, unique=True)
#     #layer = models.ForeignKey(Layer, blank=False, null=False, unique=True)
#     searchable = models.BooleanField(_('Searchable?'), default=False)
#     in_gazetteer = models.BooleanField(_('In Gazetteer?'), default=False)
#     is_gaz_start_date = models.BooleanField(_('Gazetteer Start Date'), default=False)
#     is_gaz_end_date = models.BooleanField(_('Gazetteer End Date'), default=False)
#     date_format = models.CharField(_('Date Format'), max_length=255, blank=True, null=True)
#
# class WorldMapLayer(Layer):
#
#     downloadable = models.BooleanField(_('Downloadable?'), blank=False, null=False, default=True)
#     """
#     Is the layer downloadable?
#     """
#
#     in_gazetteer = models.BooleanField(_('In Gazetteer?'), blank=False, null=False, default=False)
#     """
#     Is the layer in the gazetteer?
#     """
#
#     gazetteer_project = models.CharField(_("Gazetteer Project"), max_length=128, blank=True, null=True)
#     """
#     Gazetteer project that the layer is associated with
#     """
#
#
#     def protected_download_links(self):
#         """Returns a list of (mimetype, URL) tuples for downloads of this data
#         in various formats."""
#
#         if not self.downloadable:
#             return None
#
#         bbox = self.llbbox_coords()
#
#         dx = float(min(180,bbox[2])) - float(max(-180,(bbox[0])))
#         dy = float(min(90,bbox[3])) - float(max(-90,bbox[1]))
#
#         dataAspect = 1 if dy == 0 else dx / dy
#
#         height = 550
#         width = int(height * dataAspect)
#
#         # bbox: this.adjustBounds(widthAdjust, heightAdjust, values.llbbox).toString(),
#
#         srs = 'EPSG:4326' # bbox[4] might be None
#         bbox_string = ",".join([str(bbox[0]), str(bbox[1]), str(bbox[2]), str(bbox[3])])
#
#         links = []
#
#         if self.resource.resource_type == "featureType":
#             def wfs_link(mime,extra_params,ext):
#                 return settings.SITEURL + "download/wfs/" + str(self.id) + "/" + ext + "?" + urllib.urlencode({
#                     'service': 'WFS',
#                     'version': '1.0.0',
#                     'request': 'GetFeature',
#                     'typename': self.typename,
#                     'outputFormat': mime,
#                     'format_options': 'charset:UTF-8' #TODO: make this a settings property?
#                 })
#
#             types = [
#                 ("zip", _("Zipped Shapefile"), "SHAPE-ZIP", {'format_options': 'charset:UTF-8'}),
#                 ("gml", _("GML 2.0"), "gml2", {}),
#                 ("gml", _("GML 3.1.1"), "text/xml; subtype=gml/3.1.1", {}),
#                 ("csv", _("CSV"), "csv", {}),
#                 ("xls", _("Excel"), "excel", {}),
#                 ("json", _("GeoJSON"), "json", {})
#             ]
#             links.extend((ext, name, wfs_link(mime, extra_params, ext)) for ext, name, mime, extra_params in types)
#         elif self.resource.resource_type == "coverage":
#             try:
#                 client = httplib2.Http()
#                 description_url = settings.SITEURL + "download/wcs/" + str(self.id)  + "/mime" + "?" + urllib.urlencode({
#                     "service": "WCS",
#                     "version": "1.0.0",
#                     "request": "DescribeCoverage",
#                     "coverage": self.typename
#                 })
#                 content = client.request(description_url)[1]
#                 doc = etree.fromstring(content)
#                 extent = doc.find(".//%(gml)slimits/%(gml)sGridEnvelope" % {"gml": "{http://www.opengis.net/gml}"})
#                 low = extent.find("{http://www.opengis.net/gml}low").text.split()
#                 high = extent.find("{http://www.opengis.net/gml}high").text.split()
#                 w, h = [int(h) - int(l) for (h, l) in zip(high, low)]
#
#                 def wcs_link(mime,ext):
#                     return settings.SITEURL + "download/wcs/" + str(self.id) + "/" + ext + "?" + urllib.urlencode({
#                         "service": "WCS",
#                         "version": "1.0.0",
#                         "request": "GetCoverage",
#                         "CRS": "EPSG:4326",
#                         "height": h,
#                         "width": w,
#                         "coverage": self.typename,
#                         "bbox": bbox_string,
#                         "format": mime
#                     })
#
#                 types = [("tif", "GeoTIFF", "geotiff")]
#                 links.extend([(ext, name, wcs_link(mime,ext)) for (ext, name, mime) in types])
#             except Exception, e:
#                 # if something is wrong with WCS we probably don't want to link
#                 # to it anyway
#                 # But at least this indicates a problem
#                 notiff = mark_safe("<del>GeoTIFF</del>")
#                 links.extend([("tiff",notiff,"#")])
#
#         def wms_link(mime, ext):
#             return settings.SITEURL + "download/wms/" + str(self.id) + "/" + ext + "?"  + urllib.urlencode({
#                 'service': 'WMS',
#                 'request': 'GetMap',
#                 'layers': self.typename,
#                 'format': mime,
#                 'height': height,
#                 'width': width,
#                 'srs': srs,
#                 'bbox': bbox_string
#             })
#
#         types = [
#             ("tiff", _("GeoTIFF"), "image/geotiff"),
#             ("jpg", _("JPEG"), "image/jpeg"),
#             ("pdf", _("PDF"), "application/pdf"),
#             ("png", _("PNG"), "image/png")
#         ]
#
#         links.extend((ext, name, wms_link(mime,ext)) for ext, name, mime in types)
#
#         kml_reflector_link_download = settings.SITEURL + "download/wms_kml/" + str(self.id) + "/kml" + "?"  + urllib.urlencode({
#             'layers': self.typename,
#             'mode': "download"
#         })
#
#         kml_reflector_link_view = settings.SITEURL + "download/wms_kml/" + str(self.id)  + "/kml" + "?" + urllib.urlencode({
#             'layers': self.typename,
#             'mode': "refresh"
#         })
#
#         links.append(("KML", _("KML"), kml_reflector_link_download))
#         links.append(("KML", _("View in Google Earth"), kml_reflector_link_view))
#
#         return links
#
# def create_layer_attribute(instance, sender, **kwargs):
#     try:
#         SearchAttribute.objects.get(attribute_ptr_id=instance.pk)
#     except:
#         la = SearchAttribute(attribute_ptr_id=instance.pk)
#         la.__dict__.update(instance.__dict__)
#         la.searchable = True if instance.attribute_type == 'xsd-string' else False
#         la.save()
#
# signals.post_save.connect(create_layer_attribute, sender=Attribute)
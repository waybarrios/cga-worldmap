from decimal import Decimal
import json
from agon_ratings.models import OverallRating
from dialogos.models import Comment

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models import Avg
from haystack import indexes

from geonode.maps.models import Layer, Map
from geonode.maps.models import Contact
from geonode.flexidates import parse_julian_date

class LayerIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    iid = indexes.IntegerField(model_attr='id')
    type = indexes.CharField(faceted=True)
    subtype = indexes.CharField(faceted=True)
    name = indexes.CharField(model_attr="title")
    description = indexes.CharField(model_attr="abstract")
    owner = indexes.CharField(model_attr="owner", faceted=True, null=True)
    created = indexes.DateTimeField(model_attr="date")
    modified = indexes.DateTimeField(model_attr="date")
    category = indexes.CharField(model_attr="topic_category", faceted=True, null=True)
    detail_url = indexes.CharField(model_attr="get_absolute_url")
    bbox_left = indexes.FloatField()
    bbox_right = indexes.FloatField()
    bbox_top = indexes.FloatField()
    bbox_bottom = indexes.FloatField()
    temporal_extent_start=indexes.CharField(model_attr="temporal_extent_start", null=True)
    temporal_extent_end=indexes.CharField(model_attr="temporal_extent_end", null=True)
    temporal_extent_start_julian = indexes.FloatField(null=True)
    temporal_extent_end_julian = indexes.FloatField(null=True)
    keywords = indexes.MultiValueField(model_attr="keyword_list", null=True)
    local = indexes.CharField(faceted=True)
    service = indexes.CharField(model_attr="service", default=settings.SITENAME, faceted=True)
    ptype = indexes.CharField(faceted=True)
    overall_rating = indexes.IntegerField(boost=1.125)
    num_ratings = indexes.IntegerField(boost=1.125)
    num_comments = indexes.IntegerField(boost=1.125)
    comments = indexes.MultiValueField(model_attr="comment_text")
    unique_views = indexes.IntegerField()
    #json = indexes.CharField(indexed=False)

    def get_model(self):
        return Layer

    def prepare_type(self, obj):
        return "layer"

    def prepare_temporal_extent_start_julian(self,obj):
        if obj.temporal_extent_start:
            return parse_julian_date(obj.temporal_extent_start)

    def prepare_temporal_extent_end_julian(self,obj):
        if obj.temporal_extent_end:
            return parse_julian_date(obj.temporal_extent_end)

    def prepare_bbox_left(self, obj):
        return obj.llbbox_coords()[0]

    def prepare_bbox_right(self, obj):
        return obj.llbbox_coords()[2]

    def prepare_bbox_bottom(self, obj):
        return obj.llbbox_coords()[1]

    def prepare_bbox_top(self, obj):
        return obj.llbbox_coords()[3]

    def prepare_local(self,obj):
        return str(obj.local).lower()

    def prepare_subtype(self, obj):
        if obj.storeType == "dataStore":
            return "vector"
        elif obj.storeType == "coverageStore":
            return "raster"
            
    def prepare_download_links(self,obj):
        try:
            links = obj.download_links()
            prepped = [(ext,name.encode(),extra) for ext,name,extra in links]
            return prepped
        except:
            return None

    def prepare_metadata_links(self,obj):
        try:
            return obj.metadata_links
        except:
            return None

    def prepare_overall_rating(self,obj):
        ct = ContentType.objects.get_for_model(obj)
        try:
            rating = OverallRating.objects.filter(
                object_id = obj.pk,
                content_type = ct
            ).aggregate(r = Avg("rating"))["r"]
            return float(str(rating or "0"))
        except OverallRating.DoesNotExist:
            return 0.0

    def prepare_num_ratings(self,obj):
        ct = ContentType.objects.get_for_model(obj)
        try:
            return OverallRating.objects.filter(
                object_id = obj.pk,
                content_type = ct
            ).all().count()
        except OverallRating.DoesNotExist:
            return 0

    def prepare_num_comments(self,obj):
        try:
            return Comment.objects.filter(
                object_id=obj.pk,
                content_type=ContentType.objects.get_for_model(obj)
            ).all().count()
        except:
            return 0


    def prepare_unique_views(self,obj):
        stats = obj.layerstats_set.all()
        if stats.count() > 0:
            return stats[0].uniques



    def prepare_json(self, obj):
        bbox = obj.llbbox if obj.llbbox else [-180, -90, 180, 90]
        try:
            poc_profile = Contact.objects.get(user=obj.poc.user)
        except:
            poc_profile = None
		
        data = {
            "_type": self.prepare_type(obj),
            "_display_type": obj.display_type,

            "id": obj.id,
            "uuid": obj.uuid,
            "last_modified": obj.date.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "title": obj.title,
            "abstract": obj.abstract,
            "subtype": self.prepare_subtype(obj),
            "title": obj.title,
            "name": obj.typename,
            "description": obj.abstract,
            "owner": obj.owner.get_full_name() if obj.owner else '',
            "owner_detail": settings.SITEURL + obj.owner.get_absolute_url() if obj.owner else '',
            "category": obj.topic_category.title if obj.topic_category else "None",
            "keywords": [keyword.name for keyword in obj.keywords.all()] if obj.keywords else [],
            #"thumb": Thumbnail.objects.get_thumbnail(obj),
            "detail_url": settings.SITEURL + obj.get_absolute_url(),  # @@@ Use Sites Framework?
            "download_links": self.prepare_download_links(obj),
            "metadata_links": self.prepare_metadata_links(obj),
            "bbox": {
                "minx": bbox[0],
                "miny": bbox[2],
                "maxx": bbox[1],
                "maxy": bbox[3],
            },
            "attribution": {
                "title": poc_profile.name if poc_profile else "",
                "href": poc_profile.get_absolute_url() if poc_profile else "",
            },
            "temporal_extent_start": obj.temporal_extent_start,
            "temporal_extent_end": obj.temporal_extent_end,
            #"temporal_extent_start_julian": self.temporal_extent_start_julian,
            #"temporal_extent_end_julian": self.temporal_extent_end,
        }

        if obj.owner:
            data.update({"owner_detail": obj.owner.get_absolute_url()})

        return json.dumps(data)


class MapIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr="title")
    iid = indexes.IntegerField(model_attr='id')
    type = indexes.CharField(faceted=True)
    # bbox_left = indexes.FloatField(model_attr='bbox_left')
    # bbox_right = indexes.FloatField(model_attr='bbox_right')
    # bbox_top = indexes.FloatField(model_attr='bbox_top')
    # bbox_bottom = indexes.FloatField(model_attr='bbox_bottom')
    abstract = indexes.CharField(model_attr='abstract')
    content = indexes.CharField(model_attr='content')
    owner = indexes.CharField(model_attr="owner", faceted=True, null=True)
    created = indexes.DateTimeField(model_attr="created_dttm")
    modified = indexes.DateTimeField(model_attr="last_modified")
    detail_url = indexes.CharField(model_attr="get_absolute_url")
    #json = indexes.CharField(indexed=False)

    def get_model(self):
        return Map

    def prepare_type(self, obj):
        return "map"

    def prepare_json(self, obj):
        data = {
            "_type": self.prepare_type(obj),
            "id": obj.id,
            "last_modified": obj.last_modified.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "title": obj.title,
            "description": obj.abstract,
            "owner": obj.owner.username,
            "keywords": [keyword.name for keyword in obj.keywords.all()] if obj.keywords else [],
            #"thumb": Thumbnail.objects.get_thumbnail(obj),
            "detail_url": obj.get_absolute_url(),
            }

        if obj.owner:
            data.update({"owner_detail": Contact.objects.get(user=obj.owner).get_absolute_url()})

        return json.dumps(data)

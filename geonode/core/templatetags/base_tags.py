from django import template

from django.db.models import Count

from agon_ratings.models import Rating
from django.contrib.contenttypes.models import ContentType

from geonode.maps.models import LayerCategory

register = template.Library()


@register.assignment_tag
def num_ratings(obj):
    ct = ContentType.objects.get_for_model(obj)
    return len(Rating.objects.filter(
                object_id = obj.pk,
                content_type = ct
    ))

    
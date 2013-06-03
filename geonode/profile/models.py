from django.db import models
from django.conf import settings
from geonode.people.models import Profile
from datetime import datetime
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
 
from django.contrib.auth.models import User, Permission
class WorldmapProfile(Profile):
    """
    WorldMapProfile (inherits Profile fields)
    """
    display_email = models.BooleanField(_('Display my email address on my profile'), blank=False, default=False, null=False)
    is_org_member = models.BooleanField(_(settings.CUSTOM_ORG_AUTH_TEXT), blank=True, null=False, default=False)
    member_expiration_dt = models.DateField(_('Affiliation expires on: '), blank=False, null=False, default=datetime.today())
     
     
@receiver(post_save, sender=User)
def user_post_save(sender, **kwargs):
    """
    Create a WorldMapProfile instance for all newly created User instances. We only
    run on user creation to avoid having to check for existence on each call
    to User.save.
    """
    user, created = kwargs["instance"], kwargs["created"]
    if created:
        profile = Profile.objects.get(user=user)
        profile.__class__ = WorldmapProfile
        profile.display_email = False
        profile.is_org_member = False
        profile.member_expiration_dt = datetime.today()
        profile.save()
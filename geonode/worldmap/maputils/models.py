from django.db import models
from geonode.maps.models import Map
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from geonode.worldmap.maputils.encode import num_encode
from geonode.worldmap.maputils.encode import despam, XssCleaner
from geonode.security.enumerations import AUTHENTICATED_USERS, ANONYMOUS_USERS, CUSTOM_GROUP_USERS
import logging
from django.utils import simplejson as json
from django.utils.html import escape

logger = logging.getLogger("geonode.maputils.models")

class WorldMap(Map):
    
    urlsuffix = models.CharField(_('Site URL'), max_length=255, blank=True)
    """
    Alphanumeric alternative to referencing maps by id, appended to end of URL instead of id, ie http://domain/maps/someview
    """

    officialurl = models.CharField(_('Official Harvard Site URL'), max_length=255, blank=True)
    """
    Full URL for official/sponsored map view, ie http://domain/someview
    """

    content = models.TextField(_('Site Content'), blank=True, null=True)
    """
    HTML content to be displayed in modal window on 1st visit
    """

    use_custom_template = models.BooleanField(_('Use a custom template'),default=False)
    """
    Whether to show default banner/styles or custom ones.
    """

    group_params = models.TextField(_('Layer Category Parameters'), blank=True)
    """
    Layer categories (names, expanded)
    """
    
    @property
    def snapshots(self):
        snapshots = MapSnapshot.objects.exclude(user=None).filter(map__id=self.map.id)
        return [snapshot for snapshot in snapshots]         
    
    def update_from_viewer(self, conf):
        """
        Update this Map's details by parsing a JSON object as produced by
        a GXP Viewer.

        This method automatically persists to the database!
        """

        Map.update_from_viewer(self, conf)
        conf = json.loads(conf)
        self.urlsuffix = escape(conf['about']['urlsuffix'])
        self.featured = conf['about'].get('featured', False)
        x = XssCleaner()
        self.content = despam(x.strip(conf['about']['introtext']))
        logger.debug("Try to save treeconfig")
        if 'groups' in conf['map']:
            self.group_params = json.dumps(conf['map']['groups'])
        logger.debug("Saved treeconfig")

        self.save()  
            
            
    def viewer_json(self, user=None, *added_layers):
        def uniqifydict(seq, item):
            """
            get a list of unique dictionary elements based on a certain  item (ie 'group').
            """
            results = []
            items = []
            for x in seq:
                if x[item] not in items:
                    items.append(x[item])
                    results.append(x)
            return results

        config =  Map.viewer_json(self, *added_layers)
        sejumps = self.jump_set.all()
        config['about']['urlsuffix'] = self.urlsuffix
        config['about']['introtext'] = self.content
        config['about']['officialurl'] = self.officialurl        
        config['social_explorer'] =[se.json() for se in sejumps]
        
        if self.group_params:
            #config["treeconfig"] = json.loads(self.group_params)
            config["map"]["groups"] = uniqifydict(json.loads(self.group_params), 'group')        
        
        return config


    def set_default_permissions(self):
        map_obj = Map.objects.get(pk=self.id)
        map_obj.set_gen_level(ANONYMOUS_USERS, map_obj.LEVEL_READ)
        map_obj.set_gen_level(AUTHENTICATED_USERS, map_obj.LEVEL_READ)
        map_obj.set_gen_level(CUSTOM_GROUP_USERS, map_obj.LEVEL_READ)

        # remove specific user permissions
        current_perms =  map_obj.get_all_level_info()
        for username in current_perms['users'].keys():
            user = User.objects.get(username=username)
            map_obj.set_user_level(user, map_obj.LEVEL_NONE)

        # assign owner admin privs
        if map_obj.owner:
            map_obj.set_user_level(map_obj.owner, map_obj.LEVEL_ADMIN)
       
            
# Create your models here.
class MapSnapshot(models.Model):
    map = models.ForeignKey(Map, related_name="snapshot_set")
    """
    The ID of the map this snapshot was generated from.
    """

    config = models.TextField(_('JSON Configuration'))
    """
    Map configuration in JSON format
    """

    created_dttm = models.DateTimeField(auto_now_add=True)
    """
    The date/time the snapshot was created.
    """

    user = models.ForeignKey(User, blank=True, null=True)
    """
    The user who created the snapshot.
    """

    def json(self):
        return {
            "map": self.map.id,
            "created": self.created_dttm.isoformat(),
            "user": self.user.username if self.user else None,
            "url": num_encode(self.id)
        }
        
class SocialExplorerLocation(models.Model):
    map = models.ForeignKey(WorldMap, related_name="jump_set")
    url = models.URLField(_("Jump URL"), blank=False, null=False, default='http://www.socialexplorer.com/pub/maps/map3.aspx?g=0&mapi=SE0012&themei=B23A1CEE3D8D405BA2B079DDF5DE9402')
    title = models.TextField(_("Jump Site"), blank=False, null=False)

    def json(self):
        logger.debug("JSON url: %s", self.url)
        return {
            "url": self.url,
            "title" :  self.title
        }
        
        
        

# # Create your models here.
# class MapSnapshot(models.Model):
#     map = models.ForeignKey(Map, related_name="snapshot_set")
#     """
#     The ID of the map this snapshot was generated from.
#     """
#
#     config = models.TextField(_('JSON Configuration'))
#     """
#     Map configuration in JSON format
#     """
#
#     created_dttm = models.DateTimeField(auto_now_add=True)
#     """
#     The date/time the snapshot was created.
#     """
#
#     user = models.ForeignKey(User, blank=True, null=True)
#     """
#     The user who created the snapshot.
#     """
#
#     def json(self):
#         return {
#             "map": self.map.id,
#             "created": self.created_dttm.isoformat(),
#             "user": self.user.username if self.user else None,
#             "url": num_encode(self.id)
#         }
#
# class SocialExplorerLocation(models.Model):
#     map = models.ForeignKey(WorldMap, related_name="jump_set")
#     url = models.URLField(_("Jump URL"), blank=False, null=False, default='http://www.socialexplorer.com/pub/maps/map3.aspx?g=0&mapi=SE0012&themei=B23A1CEE3D8D405BA2B079DDF5DE9402')
#     title = models.TextField(_("Jump Site"), blank=False, null=False)
#
#     def json(self):
#         logger.debug("JSON url: %s", self.url)
#         return {
#             "url": self.url,
#             "title" :  self.title
#         }
#
#
#
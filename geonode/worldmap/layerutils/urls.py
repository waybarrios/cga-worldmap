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

from django.conf.urls.defaults import *
import geonode.layers.views


urlpatterns = patterns(
    'geonode.worldmap.layerutils.views',
    (r'^addgeonodelayer/?$', 'addLayerJSON'),
    url(r'^(?P<layername>[^/]*)/metadata$', 'layer_metadata',name="layer_metadata"),
    url(r'^create_pg_layer', 'create_pg_layer', name='create_pg_layer'),
    (r'', include('geonode.layers.urls')),
)

# urlpatterns += patterns(
#     'geonode.worldmap.uploadutils.views',
#     (r'', include('geonode.layers.urls')),
# )


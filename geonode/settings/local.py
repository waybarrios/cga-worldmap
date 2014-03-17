from .base import *

# Enter local settings

SITENAME = "WorldMap Test"


BROKER_URL = "django://"
USE_QUEUE = False
if USE_QUEUE:
    import djcelery
    djcelery.setup_loader()
    2.4
OGP_URL = "http://geodata.tufts.edu/solr/select"
HGL_VALIDATION_KEY="OPENGEOPORTALROCKS"

GEONODE_CLIENT_LOCATION = "http://localhost:9090/"

#Import uploaded shapefiles into a database such as PostGIS?
DB_DATASTORE = True

#
#Database datastore connection settings
#
DB_DATASTORE_DATABASE = 'wmdata'
DB_DATASTORE_USER = 'wm_user'
DB_DATASTORE_PASSWORD = 'wm_password'
DB_DATASTORE_HOST = 'localhost'
DB_DATASTORE_PORT = '5432'
DB_DATASTORE_TYPE = 'postgis'
# Name of the store in geoserver
DB_DATASTORE_NAME = 'wmdata'
DB_DATASTORE_ENGINE = 'django.contrib.gis.db.backends.postgis'

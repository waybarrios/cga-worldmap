from .base import * 


SITENAME = "WorldMap Test"

SITEURL = "http://localhost/"

# GeoServer information

# The FULLY QUALIFIED url to the GeoServer instance for this GeoNode.
GEOSERVER_BASE_URL = "http://localhost/geoserver/"


# The FULLY QUALIFIED url to the GeoNetwork instance for this GeoNode
GEONETWORK_BASE_URL = "http://localhost/geonetwork/"



QUEUE_INTERVAL = '*/10'


BROKER_URL = "django://"
USE_QUEUE = True
if USE_QUEUE:
    import djcelery
    djcelery.setup_loader()

OGP_URL = "http://geodata.tufts.edu/solr/select"
HGL_VALIDATION_KEY="OPENGEOPORTALROCKS"

#GEONODE_CLIENT_LOCATION = "http://localhost:9090/"

# Defines settings for development
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'wm_db_services',
        'USER': 'wm_user',
        'PASSWORD': 'wm_password',
        'HOST': 'localhost', 'PORT': '5432'
    }
}

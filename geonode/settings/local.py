from .base import *

#Enter local settings here

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'wm_db_django15',
        'USER': 'wm_user',
        'PASSWORD': 'wm_password',
        'HOST': 'localhost', 'PORT': '5432'
        }
}

GEONODE_CLIENT_LOCATION = "http://localhost:9090/"
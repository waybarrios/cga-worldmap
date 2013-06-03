# Defines settings for development
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'wm20',
        'USER': 'wm_user',
        'PASSWORD': 'wm_password',
        'HOST': 'localhost', 'PORT': '5432'
        }
}

#Email settings (example gmail account) for registration, passwords, etc
DEFAULT_FROM_EMAIL = 'mrbertrand@gmail.com'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'mrbertrand@gmail.com'
EMAIL_HOST_PASSWORD = '@makihi69gmail1'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Settings for Social Apps
AUTH_PROFILE_MODULE = 'profile.WorldMapProfile'
REGISTRATION_OPEN = True
#If you want to redirect members of your organization to a separate authentication system when registering, change the following settings
#If you want to set another level of group permissions access, change these two settings


#If you want to redirect members of your custom group to a separate authentication system when registering, change the following settings
USE_CUSTOM_ORG_AUTHORIZATION = True
CUSTOM_GROUP_NAME = 'Harvard Users'
CUSTOM_ORG_AUTH_TEXT = 'Are you affiliated with Harvard University?'
#URL to redirect to if user indicates they are a member of your custom group
CUSTOM_ORG_AUTH_URL = 'http://about.worldmap.harvard.edu/icb/icb.do?keyword=k28501&pageid=icb.page129893&pageContentId=icb.pagecontent795722&state=maximize&login=yes'
CUSTOM_AUTH_COOKIE = 'Harvard-University-PIN-SCookie'
LOGIN_REDIRECT_URL = "/maps"
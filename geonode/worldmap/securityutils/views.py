# Create your views here.
from geonode.security.enumerations import ANONYMOUS_USERS,  AUTHENTICATED_USERS, CUSTOM_GROUP_USERS
from django.utils import simplejson as json

def _perms_info_email(obj, level_names):
    info = obj.get_all_level_info_by_email()
    # these are always specified even if none
    info[ANONYMOUS_USERS] = info.get(ANONYMOUS_USERS, obj.LEVEL_NONE)
    info[AUTHENTICATED_USERS] = info.get(AUTHENTICATED_USERS, obj.LEVEL_NONE)
    info[CUSTOM_GROUP_USERS] = info.get(CUSTOM_GROUP_USERS, obj.LEVEL_NONE)
    info['users'] = sorted(info['users'].items())
    info['names'] = sorted(info['names'].items())
    info['levels'] = [(i, level_names[i]) for i in obj.permission_levels]
    if hasattr(obj, 'owner') and obj.owner is not None:
        info['owner'] = obj.owner.username
        info['owner_email'] = obj.owner.email
    return info

def _perms_info_email_json(obj, level_names):
    return json.dumps(_perms_info_email(obj, level_names))
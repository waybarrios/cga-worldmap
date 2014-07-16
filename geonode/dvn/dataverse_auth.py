from django.conf import settings

def has_proper_auth(request):
    """For now, check for DV_TOKEN.
    Future: IP + DV_TOKEN
    Future: oauth
    """
    if not request:
        return false
    
    qdict = QueryDict(request.body)

    dv_token = qdict.get('token', None)
    
    if not dv_token == settings.DVN_TOKEN:
        return False

    return True

from django.conf import settings
from django.http import QueryDict

TOKEN_KEY_NAME = 'geoconnect_token'

def has_proper_auth(request):
    """For now, check for DV_TOKEN.
    Future: IP + DV_TOKEN
    Future: oauth
    """
    print ('has_proper_auth?')
    if not request:
        return false
    
    # Find the token
    if request.POST:
        dv_token = request.POST.get(TOKEN_KEY_NAME, None)
        print request.POST
    elif request.GET:
        dv_token = request.GET.get(TOKEN_KEY_NAME, None)
    else:
        return False
    
    if not dv_token == settings.DVN_TOKEN:
        return False

    return True

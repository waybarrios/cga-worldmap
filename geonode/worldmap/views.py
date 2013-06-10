from django.http import HttpResponse
from django.utils import simplejson as json
from django.contrib.auth.models import User
from django.db.models import Q

def ajax_lookup_email(request):
    if request.method != 'POST':
        return HttpResponse(
            content='ajax user lookup requires HTTP POST',
            status=405,
            mimetype='text/plain'
        )
    elif 'query' not in request.POST:
        return HttpResponse(
            content='use a field named "query" to specify a prefix to filter usernames',
            mimetype='text/plain'
        )
    users = User.objects.filter(Q(username__startswith=request.POST['query']) | Q(email__startswith=request.POST['query']))
    json_dict = {
        'users': [({'email': u.email, 'username':u.username}) for u in users],
        'count': users.count(),
    }
    return HttpResponse(
        content=json.dumps(json_dict),
        mimetype='text/plain'
    )
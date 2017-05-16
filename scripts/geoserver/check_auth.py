# import io, sys
import requests
import json

auth_is_ok = False
url = 'https://worldmap.harvard.edu/accounts/login/'

s = requests.Session()

r1 = s.get('https://worldmap.harvard.edu/accounts/login',  verify=False)
csrftoken = r1.cookies['csrftoken']

formdata = {'username': 'myuser', 'password':'mypassword', 'csrfmiddlewaretoken': csrftoken}
headers = dict(Referer=url)
r2 = s.post(url, data=formdata, headers=headers) # , cookies=r1.cookies)

url = 'http://worldmap.harvard.edu/geoserver/geonode/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=geonode:ukr_hotspots_7jf&maxFeatures=50&outputFormat=json'

r3 = s.get(url, verify=False)

if r3.status_code == 200:
    if not 'ServiceExceptionReport' in r3.content:
        auth_is_ok = True

print auth_is_ok

import re
import urllib

if __name__=='__main__':
    import os, sys
    DJANGO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(DJANGO_ROOT)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings.local'
    
from django import forms
from geonode.maps.models import Layer

"""
http://localhost:8000/gs/rest/sldservice/geonode:boston_social_disorder_pbl/classify.xml?attribute=STATE&method=uniqueInterval&intervals=5&ramp=Custom&startColor=%23f7fbff&endColor=%2308306b&reverse=

 http://localhost:8000/gs/rest/sldservice/geonode:boston_social_disorder_pbl/classify.xml?
    attribute=Violence_4
	&method=equalInterval
	&intervals=5
	&ramp=Gray
	&startColor=%23FEE5D9
	&endColor=%23A50F15
	&reverse=
"""
class SLDHelperForm(forms.Form):
    
    SLD_ATTRIBUTES = ['attribute', 'method', 'intervals', 'ramp', 'startColor', 'endColor', 'reverse']

    VALID_METHODS = ['uniqueInterval',  'equalInterval', 'quantile', 'jenks']
    VALID_COLOR_RAMP_VALS =  ['Blue', 'Red', 'Orange', 'Jet', 'Gray', 'Random', 'Custom']

    layer_name = forms.CharField(max_length=255)
    attribute = forms.CharField(max_length=100)
    method = forms.CharField(max_length=50)
    intervals = forms.IntegerField(required=False)
    ramp = forms.CharField(max_length=40)
    reverse = forms.BooleanField(initial=False, required=False)

    startColor =forms.CharField(max_length=7)   # irregular naming convention used to match the outgoing url string
    endColor =forms.CharField(max_length=7)     # irregular naming convention used to match the outgoing url string


    def get_url_params_str(self):
        """Build most of the url for the sldservice
        
        # /rest/sldservice/geonode:boston_social_disorder_pbl/classify.xml?attribute=Violence_4&method=equalInterval&intervals=5&ramp=Gray&startColor=%23FEE5D9&endColor=%23A50F15&reverse=
        """
        if not self.is_valid():
            return None
        
        params = self.cleaned_data.copy()
        params.pop('layer_name')    # not needed for url query string
        encoded_params = urllib.urlencode(params)
        
        url = 'rest/sldservice/geonode:%s/classify.xml?%s' % (self.cleaned_data.get('layer_name', None), encoded_params)

        return url 

    def is_valid_hex_color_val(self, hex_color_val):
        if not hex_color_val:
            return False
    
        # hex color pattern
        pattern = '^#(?:[0-9a-fA-F]{3}){1,2}$'
        if re.match(pattern, hex_color_val):
            return True
        return False
     
     
    def clean_intervals(self):        
        num_intervals = self.cleaned_data.get('intervals', -1)
        
        if not(type(num_intervals)) == int:
            raise forms.ValidationError("This number of intervals must be an integer: %s" % num_intervals)
            
        if num_intervals < 1:
            raise forms.ValidationError("This is not a valid number of intervals: %s" % num_intervals)
            
        return num_intervals
        
        
    def clean_startColor(self):        
        c = self.cleaned_data.get('startColor', None)
        if not self.is_valid_hex_color_val(c):
            raise forms.ValidationError("This is not a valid start color: %s" % c)
        return c


    def clean_endColor(self):        
        c = self.cleaned_data.get('endColor', None)
        if not self.is_valid_hex_color_val(c):
            raise forms.ValidationError("This is not a valid end color: %s" % c)
        return c
        

    def clean_method(self):
        method = self.cleaned_data.get('method', None)
        
        if not method in self.VALID_METHODS:
            raise forms.ValidationError("This is not a valid method: %s" % method)
        return method

    def clean_reverse(self):
        reverse = self.cleaned_data.get('reverse', None)

        if reverse == '':
            reverse = False

        if not reverse in (True, False):
            raise forms.ValidationError("This is not a valid value for reverse (should be true or false): \"%s\"" % reverse)

        if reverse is True:
            return 'true'
        
        return ''


    def get_error_list(self):
        if not self.errors:
            return None
            
        err_list = []
        for err_tuple in self.errors.items():
            field_name, err_list = err_tuple
            for err in err_list:
                err_list.append('%s: %s' % (field_name, err))
        return err_list


    def clean_ramp(self):
        ramp = self.cleaned_data.get('ramp', None)

        if not ramp in self.VALID_COLOR_RAMP_VALS:
            raise forms.ValidationError("This is not a valid color ramp: %s" % ramp)
        return ramp

    

if __name__=='__main__':
    d = dict(layer_name='boston_social_disorder_pbl'\
                , attribute='Income'\
                ,method='equalInterval'\
                ,intervals=5\
                ,ramp='Gray'\
                ,startColor='#FEE5D9'\
                ,endColor='#A50F15'\
                ,reverse=''\
            )
            
    f = SLDHelperForm(d)
    if f.is_valid():
        print 'valid'
        print f.cleaned_data
        print f.get_url_params_str()
    else:
        #print f.errors.items()
        for err_tuple in f.errors.items():
            field_name, err_list = err_tuple
            for err in err_list:
                print field_name, err
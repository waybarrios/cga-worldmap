from __future__ import print_function

"""
from http://stackoverflow.com/questions/27265939/comparing-python-dictionaries-and-nested-dictionaries
"""
def compare_dictionaries(dict_1, dict_2, dict_1_name, dict_2_name, path=""):
    """Compare two dictionaries recursively to find non mathcing elements

    Args:
        dict_1: dictionary 1
        dict_2: dictionary 2

    Returns:

    """
    err = ''
    key_err = ''
    value_err = ''
    old_path = path
    for k in dict_1.keys():
        print ('>> checking key: %s' % k)
        path = old_path + "[%s]" % k
        if not dict_2.has_key(k):
            print ('    ...no key found in dict 2')
            key_err += "Key %s%s not in %s\n" % (dict_2_name, path, dict_2_name)
        else:
            if isinstance(dict_1[k], dict) and isinstance(dict_2[k], dict):
                print ('--check inner level--')
                err += compare_dictionaries(dict_1[k],dict_2[k],'d1','d2', path)
            else:
                print ('compare values for: %s' % k)
                if dict_1[k] != dict_2[k]:
                    value_err += "Value of %s%s (%s) not same as %s%s (%s)\n"\
                        % (dict_1_name, path, dict_1[k], dict_2_name, path, dict_2[k])

    for k in dict_2.keys():
        path = old_path + "[%s]" % k
        if not dict_1.has_key(k):
            key_err += "Key %s%s not in %s\n" % (dict_2_name, path, dict_1_name)

    return key_err + value_err + err


#a = compare_dictionaries(d1,d2,'d1','d2')

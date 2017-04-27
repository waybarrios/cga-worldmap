from __future__ import print_function

from os.path import abspath, dirname, isfile, join, isdir, realpath
from unittest import skip

from django.utils import unittest
from django.conf import settings

from bs4 import BeautifulSoup

from geonode.contrib.dataverse_styles.style_rules_formatter import StyleRulesFormatter
from geonode.contrib.msg_util import msg, msgt

from compare_dicts import compare_dictionaries


class StyleFormatterTestCase(unittest.TestCase):
    """Test style formatting for Points vs Polygons"""

    def setUp(self):
        settings.DEBUG = True
        self.test_file_dir = join(dirname(realpath(__file__)), 'input')
        assert isdir(self.test_file_dir),\
            'Input directory not found: %s' % self.test_file_dir

    def get_input_file(self, fname):
        """Convenience method for opening a test input file"""
        full_fname = join(self.test_file_dir, fname)

        msg('open input file: %s' % full_fname)
        assert isfile(full_fname),\
            "Test input directory not found: %s" % full_fname

        fh = open(full_fname, 'r')
        content = fh.read()
        fh.close()
        return content


    def test_01_style_formatter(self):
        msgt('test_01_style_formatter')
        extra_kwargs = dict(\
                is_point_layer=True,
                current_sld=self.get_input_file('01_current_sld.xml'),
                predefined_id='abc1234')

        sld_formatter = StyleRulesFormatter('centroid_alt_123',
                                            **extra_kwargs)

        sld_rule_data = self.get_input_file('02_sld_rules.xml')

        #print(sld_rule_data)
        sld_formatter.format_sld_xml(sld_rule_data)

        self.assertEqual(sld_formatter.err_found, False)

        new_sld_xml = sld_formatter.formatted_sld_xml
        new_sld_xml_pretty = BeautifulSoup(new_sld_xml, "xml").prettify()
        #msg(new_sld_xml_pretty)
        #open(join(self.test_file_dir, 'new_sld_xml_pretty.xml'), 'w').write(new_sld_xml_pretty.strip())

        #expected_sld = self.get_input_file('03_full_sld.xml')
        #expected_sld_pretty = BeautifulSoup(expected_sld, "xml").prettify()
        expected_sld_pretty = self.get_input_file('expected_sld_pretty.xml')
        #open('expected_sld_pretty.xml', 'w').write(expected_sld_pretty)

        #self.assertEqual(new_sld_xml_pretty, expected_sld_pretty)

        import xmltodict

        new_dict = xmltodict.parse(new_sld_xml_pretty, process_namespaces=True)
        expected_dict = xmltodict.parse(expected_sld_pretty, process_namespaces=True)
        #import ipdb; ipdb.set_trace()
        #msgt(new_dict)
        #msgt(expected_dict)

        dict_diff = compare_dictionaries(new_dict, expected_dict, 'new_dict', 'expected_dict')
        msgt(dict_diff)

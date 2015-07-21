from django.core.management.base import NoArgsCommand
from geonode.ogpsearch import utils

from geonode.services.tests import ServicesTests

class Command(NoArgsCommand):
    help = """
    import data from Tufts Solr instance to WorldMap Solr
    """

    def handle_noargs(self, **options):
        utils.OGP_utils.solr_to_solr()



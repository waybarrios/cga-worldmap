from django.core.management.base import NoArgsCommand
from geonode.ogpsearch import utils

from geonode.services.tests import ServicesTests

class Command(NoArgsCommand):
    help = """
    """

    def handle_noargs(self, **options):
        utils.OGP_utils.geonode_to_solr()



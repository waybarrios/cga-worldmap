from geoserver.catalog import _name, Catalog, FailedRequestError, ConflictingDataError, UploadError
from geoserver.support import prepare_upload_bundle as prepare_shapefile_bundle
from os import unlink
from zipfile import ZipFile
from tempfile import mkstemp
from geoserver.support import url
import logging

logger = logging.getLogger("geonode.maps.worldmap_gsconfig")

### start gsconfig.py overrides ###



def prepare_upload_bundle(name, data):
    """GeoServer's REST API uses ZIP archives as containers for file formats such
    as Shapefile and WorldImage which include several 'boxcar' files alongside
    the main data.  In such archives, GeoServer assumes that all of the relevant
    files will have the same base name and appropriate extensions, and live in
    the root of the ZIP archive.  This method produces a zip file that matches
    these expectations, based on a basename, and a dict of extensions to paths or
    file-like objects. The client code is responsible for deleting the zip
    archive when it's done."""
    # handle, f = mkstemp() # we don't use the file handle directly. should we?
    f = mkstemp()[1]
    """Create ZipFile object from uploaded data """
    oldf = open(data, 'r')
    oldzip = ZipFile(oldf)

    """New zip file"""
    noo = open(f, "wb")
    newzip = ZipFile(f, "w")

    """Get the necessary files from the uploaded zip, and add them to the new zip
    with the desired layer name"""
    zipFiles = oldzip.namelist()
    files = ['.shp', '.prj', '.shx', '.dbf', '.sld']
    fname = "%s" % (name)
    for file in zipFiles:
        ext = file[-4:].lower()
        if ext in files:
            files.remove(ext) #OS X creates hidden subdirectory with garbage files having same extensions; ignore.
            logger.debug("================Write [%s].[%s]", fname, ext)
            newzip.writestr(name + ext, oldzip.read(file))
    return f

class InvalidAttributesError(Exception):
    pass   

class WorldmapCatalog(Catalog):
    
    def create_featurestore(self, name, data, workspace=None, overwrite=False, charset=None):
        if not isinstance(data,dict):
            logger.debug('Data is a zipfile')
            data = prepare_upload_bundle(name, data)
        Catalog.create_featurestore(self, name, data, workspace=None, overwrite=False, charset=None)    
    
    def add_data_to_store(self, store, name, data, workspace=None, overwrite = False, charset = None):
        if isinstance(store, basestring):
            store = self.get_store(store, workspace=workspace)
        if workspace is not None:
            workspace = _name(workspace)
            assert store.workspace.name == workspace, "Specified store (%s) is not in specified workspace (%s)!" % (store, workspace)
        else:
            workspace = store.workspace.name
        store = store.name

        if isinstance(data, dict):
            bundle = prepare_shapefile_bundle(name, data)
        else:
            bundle = prepare_upload_bundle(name,data)

        params = dict()
        if overwrite:
            params["update"] = "overwrite"
        if charset is not None:
            params["charset"] = charset

        message = open(bundle)
        headers = { 'Content-Type': 'application/zip', 'Accept': 'application/xml' }
        upload_url = url(self.service_url, 
            ["workspaces", workspace, "datastores", store, "file.shp"], params) 

        try:
            headers, response = self.http.request(upload_url, "PUT", message, headers)
            self._cache.clear()
            if headers.status != 201:
                raise UploadError(response)
        finally:
            unlink(bundle)    
    
    
    def create_native_layer(self, workspace, store, name,
          native_name, title, srs, attributes):
        """
        Physically create a layer in one of GeoServer's datastores.
        For example, this will actually create a table in a Postgis store.

        Parameters include:
        workspace - the Workspace object or name of the workspace of the store to
           use
        store - the Datastore object or name of the store to use
        name - the published name of the store
        native_name - the name used in the native storage format (such as a
                filename or database table name)
        title - the title for the created featuretype configuration
        srs - the SRID for the SRS to use (like "EPSG:4326" for lon/lat)
        attributes - a dict specifying the names and types of the attributes for
           the new table.  Types should be specified using Java class names:

           * boolean = java.lang.Boolean
           * byte = java.lang.Byte
           * timestamp = java.util.Date
           * double = java.lang.Double
           * float = java.lang.Float
           * integer = java.lang.Integer
           * long = java.lang.Long
           * short = java.lang.Short
           * string = java.lang.String
        """
        if isinstance(workspace, basestring):
                ws = self.get_workspace(workspace)
        elif workspace is None:
                ws = self.get_default_workspace()
        ds = self.get_store(store, ws)
        existing_layer = self.get_resource(name, ds, ws) 
        if existing_layer is not None:
                msg = "There is already a layer named %s in %s" % (name, workspace)
                raise ConflictingDataError(msg)
        if len(attributes) < 1:
                msg = "The specified attributes are invalid"
                raise InvalidAttributesError(msg)

        has_geom = False
        attributes_block = "<attributes>"
        empty_opts = {}
        for spec in attributes:
                if len(spec) == 2:
                        att_name, binding = spec
                        opts = empty_opts
                elif len(spec) == 3:
                        att_name, binding, opts = spec
                else:
                        raise InvalidAttributesError("expected tuple of (name,binding,dict?)")

                nillable = opts.get("nillable",False)

                if binding.find("com.vividsolutions.jts.geom") >= 0:
                        has_geom = True

                attributes_block += ("<attribute>"
                        "<name>{name}</name>"
                        "<binding>{binding}</binding>"
                        "<nillable>{nillable}</nillable>"
                        "</attribute>").format(name=att_name, binding=binding, nillable=nillable)
        attributes_block += "</attributes>"

        if has_geom == False:
                msg = "Geometryless layers are not currently supported"
                raise InvalidAttributesError(msg)

        xml = ("<featureType>"
                        "<name>{name}</name>"
                        "<nativeName>{native_name}</nativeName>"
                        "<title>{title}</title>"
                        "<srs>{srs}</srs>"
                        "{attributes}"
                        "</featureType>").format(name=name.encode('UTF-8','strict'), native_name=native_name.encode('UTF-8','strict'), 
                                                                                title=title.encode('UTF-8','strict'), srs=srs,
                                                                                attributes=attributes_block)
        headers = { "Content-Type": "application/xml" }
        url = '%s/workspaces/%s/datastores/%s/featuretypes?charset=UTF-8' % (self.service_url, ws.name, store)
        headers, response = self.http.request(url, "POST", xml, headers)
        assert 200 <= headers.status < 300, "Tried to create PostGIS Layer but got " + str(headers.status) + ": " + response
        self._cache.clear()
        return self.get_resource(name)
    
### end gsconfig.py overrides ###
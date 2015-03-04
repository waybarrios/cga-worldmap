if (typeof OpenGeoportal == 'undefined'){
	OpenGeoportal = {};
} else if (typeof OpenGeoportal != "object"){
    throw new Error("OpenGeoportal already exists and is not an object");
}

if (typeof OpenGeoportal.Models == 'undefined'){
	OpenGeoportal.Models = {};
} else if (typeof OpenGeoportal.Models != "object"){
    throw new Error("OpenGeoportal.Models already exists and is not an object");
}


OpenGeoportal.Models.ResultItem = Backbone.Model.extend({
	//there are some cases where the LayerId doesn't make a good id for a Backbone model
    //idAttribute: "LayerId"

});

OpenGeoportal.ResultCollection = Backbone.Collection.extend({
	model: OpenGeoportal.Models.ResultItem
});

//collection for the bbview results table (to replace above)
OpenGeoportal.ResultsCollection = Backbone.Collection.extend({
	model: OpenGeoportal.Models.ResultItem,
	initialize: function(){
		if (this.searcher === null){
			this.searcher = OpenGeoportal.ogp.appState.get("queryTerms"); 
		}
	},
	
    fetchOn: false,
	searcher: null,
	url : function(){
		return this.searcher.getSearchRequest();
		},

	totalResults: 0,
    parse: function(resp) {
        return this.solrToCollection(resp);
      },
		// converts solr response object to backbone models
	solrToCollection: function(dataObj) {
			// dataObj is a Javascript object (usually) returned by Solr
			this.totalResults = dataObj.response.numFound;
			var start = dataObj.response.start;
			var solrLayers = dataObj.response.docs;
			var ids = [];
			var previewed = OpenGeoportal.ogp.appState.get("previewed").each(function(model){
				if (model.get("preview") === "on"){
					ids.push(model.get("LayerId"));
				}
			});
			// temp code to pull out heatmap png from solr response and display
			removeHeatmap();
			tempResponse = dataObj;
			var facetCounts = tempResponse.facet_counts;
			var facetHeatmaps = facetCounts.facet_heatmaps;
			var bbox_rpt = facetHeatmaps.bbox_rpt;

			var heatmap = bbox_rpt[15];
			if (heatmap != null)
			    drawHeatmap(bbox_rpt);

			// create Image object to get png width and height
			// layer creation based on
			//   http://gis.stackexchange.com/questions/58607/displaying-a-multi-zoom-image-layer-in-open
			/* old code to display Solr heatmap png
			heatmapPng = bbox_rpt[15];
			img = new Image();
			img.src = "data:image/png;base64," + heatmapPng;
			bounds = OpenGeoportal.ogp.map.getExtent().transform(OpenGeoportal.ogp.map.projection, new OpenLayers.Projection("EPSG:4326"));
			bounds2 = OpenGeoportal.ogp.map.getExtent();
			heatmapLayer = new OpenLayers.Layer.Image( 'Heatmap', "data:image/png;base64," + heatmapPng,
								  new OpenLayers.Bounds(bounds2.left,bounds2.bottom,bounds2.right,bounds2.top), 
								  new OpenLayers.Size(img.width, img.height),
                                  {opacity: 0.7});

			OpenGeoportal.ogp.map.addLayer(heatmapLayer);
			console.log("added heapmap layer to map");
            */
			// solr docs holds an array of hashtables, each hashtable contains a
			// layer
			var arrModels = [];
			
			_.each(solrLayers, function(solrLayer){

				solrLayer.resultNum = start;
				start++;
				
				//filter out layers in the preview pane

				if (_.contains(ids, solrLayer.LayerId)){
					solrLayer.hidden = true;
				}
				
				//just parse the json here, so we can use the results elsewhere
				var locationParsed = {};
				try {
					var rawVal = solrLayer.Location;
					if (rawVal.length > 2){
						locationParsed = jQuery.parseJSON(rawVal);
					}
				} catch (err){
					console.log([solrLayer["LayerId"], err]);
				}
				solrLayer.Location = locationParsed;
				
				arrModels.push(solrLayer);
			});
			return arrModels;
		},
	    
		
		enableFetch: function() {
		      this.fetchOn = true;
		    },

		disableFetch: function() {
		      this.fetchOn = false;
		    },
		
		extraParams: {
			//does this get added by solr object?
		},
		
		pageParams: {
			start: 0,
			rows: 50
		},
		
		fetchStatus: null,
		
		newSearch: function(){
			if (!this.fetchOn && typeof this.fetchStatus !== "undefined" && this.fetchStatus !== null){
				console.log("abort called");
				this.fetchStatus.abort();
			}
			
	        this.disableFetch();
	        this.pageParams.start = 0;
	        var that = this;

	        var xhr = this.fetch({
	          dataType: "jsonp",
			  jsonp: "json.wrf",
	          complete: function(){that.fetchComplete.apply(that, arguments); jQuery(document).trigger("newResults");},
	          reset: true,
	          data: $.extend(this.pageParams, this.extraParams)
	        });
	        this.fetchStatus = xhr;
	        return xhr;
		},
		
		nextPage: function(){
			if (!this.fetchOn){
				return;
			}
			
	       this.disableFetch();
	        
	       this.pageParams.start = this.last().get("resultNum") + 1;
	       
	       if (this.pageParams.start > this.totalResults){
	    	   return;
	       }
	       var that = this;
	       this.fetchStatus = this.fetch({
	          dataType: "jsonp",
			  jsonp: "json.wrf",

	         // success: this.fetchSuccess,
	         // error: this.fetchError,
	          complete: function(){that.fetchComplete.apply(that, arguments);},
	          remove: false,
	          data: $.extend(this.pageParams, this.extraParams)
	        });
		},


		fetchComplete: function(){
			this.enableFetch();
		}

});

function drawBox()
{

    boxes  = new OpenLayers.Layer.Boxes("Boxes")
    //coordinates = [boundingbox.left, boundingbox.bottom,boundingbox.right, boundingbox.top]
    coordinates = [10, 10, 20, 20];

    bounds = OpenLayers.Bounds.fromArray(coordinates).transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"))
    box = new OpenLayers.Marker.Box(bounds, null, style)
    ///box.setBorder("blue")
    box.setStyle(style);
    boxes.addMarker(box)
    OpenGeoportal.ogp.map.addLayers([boxes])
}

function drawBox2()
{
var style = {
   strokeColor: "#00FF00",
   strokeOpacity: 1,
   strokeWidth: 0,
   fillColor: "#FF0000",
   fillOpacity: 0.3
    };
    layer = new OpenLayers.Layer.Vector("boxes");
    coordinates = [10, 10, 20, 20];
    bounds = OpenLayers.Bounds.fromArray(coordinates).transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));
    box = new OpenLayers.Feature.Vector(bounds.toGeometry(), null, style);
    layer.addFeatures(box);

style = {
   strokeColor: "#00FF00",
   strokeOpacity: 1,
   strokeWidth: 0,
   fillColor: "#00FF00",
   fillOpacity: 0.6
    };
    coordinates = [20, 20, 30, 30];
    bounds = OpenLayers.Bounds.fromArray(coordinates).transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));
    style.fillColor = "#00FF00";
    box = new OpenLayers.Feature.Vector(bounds.toGeometry(), null, style);
    layer.addFeatures(box);

    OpenGeoportal.ogp.map.addLayers([layer]);

}

function removeHeatmap()
{
    if (heatmapLayer != null)
	{
	    console.log("removing layer");
		OpenGeoportal.ogp.map.removeLayer(heatmapLayer);
		heatmapLayer = null;
	}
}

// this variable should be moved
// perhaps as a member variable in a heatmap object
heatmapLayer = null;

/**
  return the largest value in the heatmap so its values can be scaled
  some elements in the heatmap can be null so we replace them with 0
*/
function heatmapMax(heatmap)
{
   var max = -1;
   for (i = 0 ; i < heatmap.length ; i++)
   {
       var currentRow = heatmap[i];
       if (currentRow == null)  heatmap[i] = currentRow = [];
       for (j = 0 ; j < currentRow.length ; j++)
       {
           if (currentRow[j] == null) currentRow[j] = 0;
           if (currentRow[j] > max)
              max = currentRow[j];
       }
   }
   return max;
}

/**
  the passed heatmap object is an array that contains the heatmap 2d array
   as well as its geodetic bounds
  the heatmap is displayed by creating a grid of translucent red rectangles
*/
function drawHeatmap(heatmapObject)
{
    heatmap = heatmapObject[15];
    var maxValue = heatmapMax(heatmap);
    if (maxValue == -1) return;  // something wrong

    var minimumLatitude = heatmapObject[11];
    var maximumLatitude = heatmapObject[13];
    var deltaLatitude = maximumLatitude - minimumLatitude;
    var minimumLongitude = heatmapObject[7];
    var maximumLongitude = heatmapObject[9];
    var deltaLongitude = maximumLongitude - minimumLongitude;

    var stepsLatitude = heatmap.length;
    var stepsLongitude = heatmap[0].length;
    var stepSizeLatitude = deltaLatitude / stepsLatitude;
    var stepSizeLongitude = deltaLongitude / stepsLongitude;
    heatmapLayer = new OpenLayers.Layer.Vector("heatmap");

    for (i = 0 ; i < stepsLatitude ; i++)
    {
        for (j = 0 ; j < stepsLongitude ; j++)
        {
            var heatmapValue = heatmap[heatmap.length - i - 1][j];
            var scaledHeatmapValue = Math.floor((heatmapValue / maxValue) * 255);
            var rgb = scaledHeatmapValue << 16;
            var color = '#' + rgb.toString(16);
            var coordinates = [minimumLongitude + (j * stepSizeLongitude), minimumLatitude + (i * stepSizeLatitude),
                           minimumLongitude + ((j+1) * stepSizeLongitude), minimumLatitude + ((i+1) * stepSizeLatitude)];
            var bounds = OpenLayers.Bounds.fromArray(coordinates).transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));
            // we should create 255 separate styles and use the right one rather than making a new style for each tile
            var style = {strokeWidth: 0, fillOpacity: 0.4};
            style.fillColor = color;
            var box = new OpenLayers.Feature.Vector(bounds.toGeometry(), null, style);
            heatmapLayer.addFeatures(box);
            if ((i == 0) && (j == 0))
                console.log(coordinates);
            if ((i == (stepsLatitude-1)) && (j == (stepsLongitude-1)))
                console.log(coordinates);
        }
    }
    OpenGeoportal.ogp.map.addLayers([heatmapLayer]);

}
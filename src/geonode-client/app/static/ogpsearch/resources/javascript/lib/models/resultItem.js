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
			tempResponse = dataObj;
			var facetCounts = tempResponse.facet_counts;
			var facetHeatmaps = facetCounts.facet_heatmaps;
			bbox_rpt = facetHeatmaps.bbox_rpt;

			var heatmap = bbox_rpt[15];
			//if (heatmap != null)
			drawHeatmapOpenLayers(bbox_rpt);

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



function removeHeatmap()
{
    if (heatmapLayer != null)
	{
		OpenGeoportal.ogp.map.removeLayer(heatmapLayer);
		heatmapLayer = null;
	}
}

// this variable should be moved
// perhaps as a member variable in a heatmap object
heatmapLayer = null;

/**
  return the largest and smallest value in the heatmap so its values can be scaled
  some elements in the heatmap can be null so we replace them with 0
*/
function heatmapMinMax(heatmap)
{
   var max = -1;
   var min = Number.MAX_VALUE;
   for (i = 0 ; i < heatmap.length ; i++)
   {
       var currentRow = heatmap[i];
       if (currentRow == null)  heatmap[i] = currentRow = [];
       for (j = 0 ; j < currentRow.length ; j++)
       {
           if (currentRow[j] == null) currentRow[j] = 0;
           if (currentRow[j] > max)
              max = currentRow[j];
           if (currentRow[j] < min)
              min = currentRow[j];
       }
   }
   return [min, max];
}

function scaleHeatmapValue(value, min, max)
{
    if (value == null) value = min;
    var tmp = value - min;
    tmp = Math.floor((tmp / (max - min)) * 255);
    return tmp;
}

function getAlpha(scaledValue)
{
    var tmp = scaledValue / 255.;
    if (tmp > .6) tmp = .6;

    return .4;
}


/**
  the passed heatmap object is an array that contains the heatmap 2d array
   as well as its geodetic bounds
  the heatmap is displayed by creating a grid of translucent red rectangles
*/
function drawHeatmap(heatmapObject)
{
    histogram = [];
    heatmap = heatmapObject[15];
    minMaxValue = heatmapMinMax(heatmap);
    minValue = minMaxValue[0];
    maxValue = minMaxValue[1];
    if (maxValue == -1) return;  // something wrong

    if ((maxValue - minValue) < (maxValue * .05))
        return;  // if there is no variation skip the heatmap

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
            try
            {
                var heatmapValue = heatmap[heatmap.length - i - 1][j];
                var scaledHeatmapValue = scaleHeatmapValue(heatmapValue, minValue, maxValue);
                if ((scaledHeatmapValue > 255) || (scaledHeatmapValue < 0) || (scaledHeatmapValue == null))
                   console.log("warning scaledHeatmapValue out of range: " + scaledHeatmapValue + ", " + heatmapValue);
                if (scaledHeatmapValue < 200)
                    scaledHeatmapValue = 0;
                var rgb = scaledHeatmapValue << 16;
                var color = '#' + rgb.toString(16);
                var coordinates = [minimumLongitude + (j * stepSizeLongitude), minimumLatitude + (i * stepSizeLatitude),
                           minimumLongitude + ((j+1) * stepSizeLongitude), minimumLatitude + ((i+1) * stepSizeLatitude)];
                var bounds = OpenLayers.Bounds.fromArray(coordinates).transform(new OpenLayers.Projection("EPSG:4326"), new OpenLayers.Projection("EPSG:900913"));
                // we should create 255 separate styles and use the right one rather than making a new style for each tile
                var alpha = getAlpha(scaledHeatmapValue);
                var style = {strokeWidth: 0, fillOpacity: alpha};
                style.fillColor = color;
                var box = new OpenLayers.Feature.Vector(bounds.toGeometry(), null, style);
                heatmapLayer.addFeatures(box);
                if (histogram[scaledHeatmapValue] == null)
                    histogram[scaledHeatmapValue] = 0;
                histogram[scaledHeatmapValue]++;
                if ((i == 0) && (j == 0))
                    console.log(coordinates);
                if ((i == (stepsLatitude-1)) && (j == (stepsLongitude-1)))
                    console.log(coordinates);
            }
            catch (error)
            {
                console.log("error making heatmap: " + error);
            }
        }
    }
    OpenGeoportal.ogp.map.addLayers([heatmapLayer]);

}

/// use the heatmap.js library
heatmapJs = null;
function drawHeatmapJs(heatmapObject)
{
    heatmap = heatmapObject[15];
    minMaxValue = heatmapMinMax(heatmap);
    minValue = minMaxValue[0];
    maxValue = minMaxValue[1];
    minimumLatitude = heatmapObject[11];
    maximumLatitude = heatmapObject[13];
    var deltaLatitude = maximumLatitude - minimumLatitude;
    minimumLongitude = heatmapObject[7];
    maximumLongitude = heatmapObject[9];
    var deltaLongitude = maximumLongitude - minimumLongitude;

    var stepsLatitude = heatmap.length;
    var stepsLongitude = heatmap[0].length;
    stepSizeLatitude = deltaLatitude / stepsLatitude;
    stepSizeLongitude = deltaLongitude / stepsLongitude;
    mapSize = OpenGeoportal.ogp.map.getSize();
    screenWidth = mapSize.w;
    screenHeight = mapSize.h;
    pointSpacingLatitude = screenHeight / stepsLatitude;
    pointSpacingLongitude = screenWidth / stepsLongitude;

    heatmapData = [];
    epsg4326 = new OpenLayers.Projection("EPSG:4326");
    epsg900913 = new OpenLayers.Projection("EPSG:900913");

    for (i = 0 ; i < stepsLatitude ; i++)
    {
        for (j = 0 ; j < stepsLongitude ; j++)
        {
            try
            {
                heatmapValue = heatmap[heatmap.length - i - 1][j];

                var x = minimumLongitude + (j * stepSizeLongitude);
                var y = minimumLatitude + (i * stepSizeLatitude);
                xGeodetic = minimumLongitude + (j * stepSizeLongitude);
                yGeodetic = minimumLatitude + (i * stepSizeLatitude);
                geodetic = new OpenLayers.LonLat(xGeodetic, yGeodetic);
                pixel = OpenGeoportal.ogp.map.getPixelFromLonLat(geodetic);
                //var point = new OpenLayers.Geometry.Point(x,y);
                //point.transform(epsg900913, epsg4326);
                if (j == 0)
                {
                    console.log(x + ", " + y + ": " + Math.floor(i*pointSpacingLongitude) + ", " + Math.floor(j*pointSpacingLatitude));
                    console.log("  " + xGeodetic + ", " + yGeodetic + ":  " + pixel.x + ", " + pixel.y);
                }
                var current = {x: Math.floor(j * pointSpacingLongitude) , y: Math.floor((stepsLatitude - i) * pointSpacingLatitude), value: heatmapValue};
                heatmapData.push(current);
            }
            catch (error)
            {
                console.log("error making heatmapjs: " + error);
            }
        }
    }
    if (heatmapJs == null)
        heatmapJs = h337.create({container: document.getElementById("map"), radius: 30, opacity: .2});
    heatmapJs.setData({data: heatmapData, max: maxValue, min: minValue});
    heatmapJs.repaint();
}



/**
    radius of heatmap point depends on how many pixels are between adjacent points
*/
function computeRadius(latitude, longitude, stepSize)
{
    mercator1 = OpenGeoportal.ogp.map.WGS84ToMercator(longitude, latitude);
    pixel1 = OpenGeoportal.ogp.map.getPixelFromLonLat(mercator1);
    mercator2 = OpenGeoportal.ogp.map.WGS84ToMercator(longitude + stepSize, latitude + stepSize);
    pixel2 = OpenGeoportal.ogp.map.getPixelFromLonLat(mercator2);
    deltaLatitude = Math.abs(pixel1.x - pixel2.x);
    return Math.ceil(deltaLatitude * 2.);
}

var heatmapFactor = .95;

/**
    process the passed array of arrays to compute a threshold value
    put all values into a new array and sort it
    the returned threshold value selected from the array
*/
function getThreshold(heatmap)
{
    tmp = [];
    for (i = 0 ; i < heatmap.length ; i++)
        tmp.push.apply(tmp, heatmap[i]);
    tmp.sort(function(a, b) {return a - b;});  // force numeric sort
    length = tmp.length;
    threshold = tmp[Math.floor(length * heatmapFactor)];
    return threshold;
}

/**
    uses openlayer-heatmap library from https://github.com/hoehrmann/openlayers-heatmap
    draw heatmap over cells containing the most documents
    the heatmap points are reset every time
*/
heatmapLayer = null;

function drawHeatmapOpenLayers(heatmapObject)
{
    if (heatmapLayer != null)
    {
        OpenGeoportal.ogp.map.removeLayer(heatmapLayer);
        heatmapLayer = null;
    }
    if (heatmapLayer == null)
        heatmapLayer = new Heatmap.Layer("Heatmap");
    console.log("number of points = " + heatmapLayer.points.length);
    heatmapLayer.points = [];  //delete any previously added points

    heatmap = heatmapObject[15];
    minMaxValue = heatmapMinMax(heatmap);
    minValue = minMaxValue[0];
    maxValue = minMaxValue[1];
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
    var radius = computeRadius(minimumLatitude, minimumLongitude, Math.max(stepSizeLatitude, stepSizeLongitude));
    var minimumThreshold = getThreshold(heatmap);
    for (i = 0 ; i < stepsLatitude ; i++)
    {
        for (j = 0 ; j < stepsLongitude ; j++)
        {
            try
            {
                var heatmapValue = heatmap[heatmap.length - i - 1][j];
                currentLongitude = minimumLongitude + (j * stepSizeLongitude) + (.5 * stepSizeLongitude);
                currentLatitude = minimumLatitude + (i * stepSizeLatitude) + (.5 * stepSizeLatitude);
                mercator = OpenGeoportal.ogp.map.WGS84ToMercator(currentLongitude, currentLatitude);
                scaledValue = scaleHeatmapValue(heatmapValue, minValue, maxValue) / 255.;
                scaledValue = Math.pow(scaledValue, 4);
                // linearly scale values to between 0 and 255
                // use power function to non-linearly adjust values
                // finally apply floor for non-zero values
                if (scaledValue > 0 && scaledValue < .04)
                    scaledValue = .04;
                heatmapLayer.addSource(new Heatmap.Source(mercator, radius*.9, scaledValue));
            }
            catch (error)
            {
                console.log("error making heatmap: " + error);
            }
        }
    }
    heatmapLayer.setOpacity(0.33);
    OpenGeoportal.ogp.map.addLayer(heatmapLayer);

}

function heatmapTest()
{
    map = new OpenLayers.Map('map2', {
                    controls: [
                        new OpenLayers.Control.Navigation(),
                        new OpenLayers.Control.PanZoomBar(),
                        new OpenLayers.Control.LayerSwitcher({'ascending':false}),
                        new OpenLayers.Control.MousePosition(),
                    ]
                    });
    var heat = new Heatmap.Layer("Heatmap");
    heat.addSource(new Heatmap.Source(new OpenLayers.LonLat(9.434, 54.740)));
    heat.addSource(new Heatmap.Source(new OpenLayers.LonLat(9.833, 54.219)));
    heat.addSource(new Heatmap.Source(new OpenLayers.LonLat(10.833, 55.219)));
    heat.addSource(new Heatmap.Source(new OpenLayers.LonLat(16.833, 56.219)));
    heat.addSource(new Heatmap.Source(new OpenLayers.LonLat(17.833, 57.219)));
    heat.defaultIntensity = 0.1;
    heat.setOpacity(0.33);
    var wms = new OpenLayers.Layer.WMS("OpenLayers WMS", "http://labs.metacarta.com/wms/vmap0", {layers: 'basic'});
    map.addLayers([wms, heat]);
    map.zoomToExtent(heat.getDataExtent());
    console.log("added heatmap");
}

/*
    var heat = new Heatmap.Layer("Heatmap");
    merc = OpenGeoportal.ogp.map.WGS84ToMercator(9.434, 54.740);
    console.log("merc = " + merc);
    heat.addSource(new Heatmap.Source(merc));

    merc = OpenGeoportal.ogp.map.WGS84ToMercator(12.434, 56.740);
    ll2 = new OpenLayers.LonLat(merc.x, merc.y);
    console.log("  merc = " + merc);
    heat.addSource(new Heatmap.Source(merc));

    OpenGeoportal.ogp.map.addLayer(heat);
    console.log("added heatmap");

    if (true == true) return;
*/
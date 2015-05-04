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
function heatmapMinMax(heatmap, stepsLatitude, stepsLongitude)
{
   var max = -1;
   var min = Number.MAX_VALUE;
   for (i = 0 ; i < stepsLatitude ; i++)
   {
       var currentRow = heatmap[i];
       if (currentRow == null)  heatmap[i] = currentRow = [];
       for (j = 0 ; j < stepsLongitude ; j++)
       {
           if (currentRow[j] == null)
               currentRow[j] = -1;
           if (currentRow[j] > max)
              max = currentRow[j];
           if (currentRow[j] < min && currentRow[j] > -1)
              min = currentRow[j];
       }
   }
   return [min, max];
}

function rescaleHeatmapValue(value, min, max)
{

    if (value == null)
        return 0;
    if (value == -1)
        return 0;
    if (value == 0)
        return 0;
    value = value * 1.0;

    if (true)
        return value / max;
    var delta = max - min;
    if (delta <= 0)
        return 0;
    if (value < min)
        return 0;
    var tmp = (value - (min - 1)) / delta;
    console.log(" " + value + ", " + tmp + " : " + min + ", " + max);
    if (tmp < 0)
        return 0;
    if (tmp > 1)
        return 1.0;
    return tmp;
}

function rescaleHeatmapValue2(value, min, max)
{
 if (value == null)
        return 0;
    if (value == -1)
        return -1;
    if (value == 0)
        return 0;
    value = value * 1.0;

    if (true)
        return value / max;
    var delta = max - min;
    if (delta <= 0)
        return 0;
    if (value < min)
        return 0;
    var tmp = (value - (min - 1)) / delta;
    console.log("   " + value + ", " + tmp + " : " + min + ", " + max);
    if (tmp < 0)
        return 0;
    if (tmp > 1)
        return 1.0;
    return tmp;
}


function scaleHeatmapValue(value, min, max)
{
    if (value == null) value = min;
    var tmp = value - min;
    tmp = Math.floor((tmp / (max - min)) * 255);
    if (tmp < 0) tmp = 0;
    if (isNaN(tmp)) tmp = 0;
    return tmp;
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


function flattenValues(heatmap)
{
    tmp = [];
    for (i = 0 ; i < heatmap.length ; i++)
        tmp.push.apply(tmp, heatmap[i]);
    return tmp;
}

function getCeilingValues(heatmap)
{
    tmp = [];
    ceilingValues = [];
    for (i = 0 ; i < heatmap.length ; i++)
        tmp.push.apply(tmp, heatmap[i]);
    tmp.sort(function(a, b) {return a - b;});  // force numeric sort
    length = tmp.length;
    ceilingValues[0] = tmp[0];
    ceilingValues[1] = tmp[Math.ceil(length * .25)];
    ceilingValues[2] = tmp[Math.ceil(length * .5)];
    ceilingValues[3] = tmp[Math.ceil(length * .75)];
    return ceilingValues;
}

/**
  for a given value and list of groups, return the appropriate group
*/
function clipValue(value, ceilingValues)
{
    if (value == null)
        return 0;
    if (value == ceilingValues[0])
        return value;
    if (value <= ceilingValues[1])
        return 0;

    for (var i = 2 ; i < ceilingValues.length ; i++)
    {
        if (value <= ceilingValues[i])
         return ceilingValues[i];
    }
    return ceilingValues[ceilingValues.length -1];
}

function clipValueIndex(value, ceilingValues)
{
    if (value == ceilingValues[0])
        return 0;

    for (var i = 0 ; i < ceilingValues.length ; i++)
    {
        if (value < ceilingValues[i])
         return i;
    }
    return ceilingValues.length -1;
}

// when the user moves the mouse we note how may documents are under the cursor
function processEvent(event)
{
    foo = event;
    pixel = event.xy;
    mercator = OpenGeoportal.ogp.map.getLonLatFromViewPortPx(pixel);
    epsg4326 = new OpenLayers.Projection("EPSG:4326");
    epsg900913 = new OpenLayers.Projection("EPSG:900913");
    point = mercator.transform(epsg900913, epsg4326);
    count = getCountGeodetic(lastHeatmapObject, point.lat, point.lon);
    message = "Number of layers = " + count;
    jQuery("#map").tooltip( "option", "content", message );
}

/**
    uses openlayer-heatmap library from https://github.com/hoehrmann/openlayers-heatmap
    draw heatmap over cells containing the most documents
    the heatmap points are reset every time
*/
heatmapLayer = null;
backgroundLayer = null;
var radiusFactor = .9;

function drawHeatmapOpenLayers(heatmapObject)
{
    lastHeatmapObject = heatmapObject;
    try
    {
        if (heatmapLayer != null)
        {
            OpenGeoportal.ogp.map.removeLayer(heatmapLayer);
            heatmapLayer = null;
        }
    }
    catch (err)
    {
        ;
    }
    if (heatmapLayer == null)
    {
        heatmapLayer = new Heatmap.Layer("Heatmap");

        jQuery("#map").attr("title", "Number of layers =     ");
        jQuery("#map").tooltip({track: true});
        //jQuery("#map").tooltip( "option", "content", "Number of layers");
        OpenGeoportal.ogp.map.events.register("mousemove", OpenGeoportal.ogp.map,
                                              function(event) {processEvent(event);}, true);
    }
    if (backgroundLayer == null)
    {
        // hack to set background layer for evaluation
        backgroundLayer = new OpenLayers.Layer.Stamen("toner-lite");
        OpenGeoportal.ogp.map.addLayer(backgroundLayer);
    }
    heatmapLayer.points = [];  //delete any previously added points

    heatmap = heatmapObject[15];
    if (heatmap == null)
        return;
    stepsLatitude = heatmapObject[5];  //heatmap.length;
    stepsLongitude = heatmapObject[3];   //heatmap[0].length;

    minMaxValue = heatmapMinMax(heatmap, stepsLatitude, stepsLongitude);
    ceilingValues = getCeilingValues(heatmap);
    minValue = minMaxValue[0];
    maxValue = minMaxValue[1];
    if (maxValue == -1) return;  // something wrong

    var minimumLatitude = heatmapObject[11];
    var maximumLatitude = heatmapObject[13];
    var deltaLatitude = maximumLatitude - minimumLatitude;
    var minimumLongitude = heatmapObject[7];
    var maximumLongitude = heatmapObject[9];
    var deltaLongitude = maximumLongitude - minimumLongitude;


    var stepSizeLatitude = deltaLatitude / stepsLatitude;
    var stepSizeLongitude = deltaLongitude / stepsLongitude;
    radius = computeRadius(minimumLatitude, minimumLongitude, Math.max(stepSizeLatitude, stepSizeLongitude));

    flattenedValues = flattenValues(heatmap);
    series = new geostats(flattenedValues);
    //series.setPrecision(6);
    jenksClassifications = series.getClassJenks(5);
    classifications = jenksClassifications;
    //classifications = [0];
    //classifications = classifications.concat(jenksClassifications);
    //colors = [0xffffff00, 0x00c9fcff, 0x0078f2ff, 0x4a2cd9ff, 0x99019aff, 0x000000ff];
    //colors = [0xffffff00, 0xffffff00, 0xffffff00, 0xffffff00, 0xffffffff, 0xa0a0a0ff, 0x808080ff, 0x000000ff];
    colors = [0x00000000, 0xfef0d9ff, 0xfdcc8aff, 0xfc8d59ff, 0xe34a33ff, 0xb30000ff];
    colorGradient = {};
    //for (var i in jenksClassifications)
    for (var i = 0 ; i < jenksClassifications.length ; i++)
    {
            value = classifications[i];
            scaledValue = rescaleHeatmapValue2(value, classifications[0], maxValue);
            if (scaledValue < 0)
                scaledValue = 0;
            colorGradient[scaledValue] = colors[i];
    }
    heatmapLayer.setGradientStops(colorGradient);

    scaledValues = [];
    clippedValues= [];
    scaledValues = [];

    for (var i = 0 ; i < stepsLatitude ; i++)
    {
        for (var j = 0 ; j < stepsLongitude ; j++)
        {
            try
            {
                heatmapValue = heatmap[heatmap.length - i - 1][j];
                currentLongitude = minimumLongitude + (j * stepSizeLongitude) + (.5 * stepSizeLongitude);
                currentLatitude = minimumLatitude + (i * stepSizeLatitude) + (.5 * stepSizeLatitude);
                mercator = OpenGeoportal.ogp.map.WGS84ToMercator(currentLongitude, currentLatitude);
                clippedValue = clipValue(heatmapValue, classifications);
                clippedValues.push(clippedValue);
                scaledValue = scaleHeatmapValue(clippedValue, classifications[1], maxValue) / 255.;
                scaledValue2 = rescaleHeatmapValue2(heatmapValue, classifications[1], maxValue);
                //scaledValue = Math.pow(scaledValue, 4);
                // linearly scale values to between 0 and 255
                // use power function to non-linearly adjust values
                // finally apply floor for non-zero values
                //if (scaledValue > 0 && scaledValue < .06)
                //    scaledValue = .06;
                if (heatmapValue > 0)
                {
                    //heatmapLayer.addSource(new Heatmap.Source(mercator, radius*.9, scaledValue));
                    heatmapLayer.addSource(new Heatmap.Source(mercator, radius*radiusFactor, scaledValue2));
                    scaledValues.push(scaledValue2);
                }
                // console.log(heatmapValue + ", " + scaledValue)
            }
            catch (error)
            {
                console.log("error making heatmap: " + error);
            }
        }
    }

    heatmapLayer.setOpacity(0.50);
    OpenGeoportal.ogp.map.addLayer(heatmapLayer);
    console.log("heatmap displayed")
}



function createStyles()
{
    colors = new Array('#e2dee6', '#c2abdd', '#9d87b6', '#735a8f', '#3d2e4e');
    styles = []
    for (i = 0 ; i < 5 ; i++)
    {
        style = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
        style.fillColor = colors[i];
        style.strokeColor = colors[i];
        styles.push(style);
    }
    return styles;
}

function getCount(heatmapObject, latitudeMercator, longitudeMercator)
{
    geodetic = OpenGeoportal.ogp.map.MercatorToWGS84(longitudeMercator, latitudeMercator);
    longitude = geodetic.lon;
    latitude = geodetic.lat;
    return getCountGeodetic(heatmapObject, latitude, longitude);
}


function getCountGeodetic(heatmapObject, latitude, longitude)
{
    var heatmap = heatmapObject[15];
    if (heatmap == null)
        return;
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

    var latitudeIndex = Math.floor((latitude - minimumLatitude) / stepSizeLatitude);
    var longitudeIndex = Math.floor((longitude - minimumLongitude) / stepSizeLongitude);

    if (latitudeIndex < 0) latitudeIndex = 0;
    if (longitudeIndex < 0) longitudeIndex = 0;
    try
    {
        var heatmapValue = heatmap[heatmap.length - latitudeIndex - 1][longitudeIndex];
        return heatmapValue;
    }
    catch (err)
    {
        console.log("error in getCount with lat = " + latitude + ", lon = " + longitude);
        console.log("  lat index = " + latitudeIndex + ", lon index = " + longitudeIndex);
        return heatmap[0][0];
    }
}



/*
if (typeof OpenGeoportal === 'undefined') {
        OpenGeoportal = {};
}
if (typeof OpenGeoportal.Models === 'undefined') {
        OpenGeoportal.Models = {};
}


OpenGeoportal.Models.Heatmap = Backbone.Model.extend(
    {
        initialize: function()
        {
            console.log("heatmap model backbone initialize");
            that = this;
            jQuery(document).on("fireSearch", function()
                {
                    console.log("heatmap fireSearch handler");
                    that.handleHeatmap();
                });
        },
        fetchOn: false,
        searcher: function() {return OpenGeoportal.ogp.search;},
        url: function()
            {
                searcher = OpenGeoportal.ogp.appState.get("queryTerms");
                solr = searcher.getBasicSearchQuery();
                solr.enableHeatmap();
                solr.addFilter(solr.createNonGlobalAreaFilter());
                url = solr.getURL();
		        return url;
		    },
		handleHeatmap: function()
		    {
                this.fetch({dataType: "jsonp", jsonp: "json.wrf",
                            reset: true,
                            complete: function(dataObj, success)
                            {
                                foo = dataObj;
                                console.log("in heatmap complete " + dataObj.responseJSON.response.numFound);
			                    var facetCounts = dataObj.responseJSON.facet_counts;
                    			if (facetCounts != null)
			                    {
  			                        var facetHeatmaps = facetCounts.facet_heatmaps;
			                        bbox_rpt = facetHeatmaps.bbox_rpt;

			                        var heatmap = bbox_rpt[15];

  			                        drawHeatmapOpenLayers(bbox_rpt);
                                }
                            }});
            }
    }

  );

*/
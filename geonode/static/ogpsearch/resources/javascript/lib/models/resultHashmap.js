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


OpenGeoportal.Models.ResultHeatmap = Backbone.Model.extend({
	defaults:
	{
	    heatmap: null,
	    minimumLatitude: null,
	    maximumLatitude: null,
	    deltaLatitude: null,
	    minimumLongitude: null,
	    maximumLongitude: null,
	    deltaLongitude = null,
	    stepSizeLatitude = null
	    stepSizeLongitude = null
	}

	constructor: function ()
	{
	    console.log("in ResultHemap constructor");
	}

	renderToMap: function()
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
		    console.log("  scaledValue = " + scaledValue + ", color = " + colors[i].toString(16));
		}
	    heatmapLayer.setGradientStops(colorGradient);

	    scaledValues = [];
	    clippedValues= [];
	    scaledValues = [];
	    /*
	      for (var i = 0 ; i < 5 ; i++)
	      for (var j = 0 ; j < 5 ; j++)
	      {
	      mercator = OpenGeoportal.ogp.map.WGS84ToMercator(i, j);
	      heatmapLayer.addSource(new Heatmap.Source(mercator, radius*radiusFactor, (i + j) / 10. ));

	      }
	    */
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
				    //clippedValue = clipValue(heatmapValue, ceilingValues);
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

			drawHeatmapOpenLayers(bbox_rpt);

            //drawHeatmapGeostatsTest(bbox_rpt);
			//drawHeatmapGeostats(bbox_rpt);

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


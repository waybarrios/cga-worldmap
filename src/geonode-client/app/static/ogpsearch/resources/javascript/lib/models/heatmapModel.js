
if (typeof OpenGeoportal === 'undefined') 
{
    OpenGeoportal = {};
}
if (typeof OpenGeoportal.Models === 'undefined') 
{
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
                    that.handleHeatmap(that);
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
		handleHeatmap: function(that)
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
					that.drawHeatmapOpenLayers(that, bbox_rpt);
				    }
				}});
		},
	deleteHeatmapLayer: function(that)
	{
	    try
	    {
		if (that.heatmapLayer != null)
		{
		    OpenGeoportal.ogp.map.removeLayer(that.heatmapLayer);
		    that.heatmapLayer = null;
		}
	    }
	    catch (err)
	    {
		;
	    }
	},
	initBackgroundLayer: function(that)
	{
	    if (that.backgroundLayer == null)
	    {
		// hack to set background layer for evaluation
		that.backgroundLayer = new OpenLayers.Layer.Stamen("toner-lite");
		OpenGeoportal.ogp.map.addLayer(that.backgroundLayer);
	    }

	},
	initHeatmapLayer: function()
	{
	    heatmapLayer = new Heatmap.Layer("Heatmap");
	    jQuery("#map").attr("title", "Number of layers =     ");
	    jQuery("#map").tooltip({track: true});
	    OpenGeoportal.ogp.map.events.register("mousemove", OpenGeoportal.ogp.map,
						  function(event) {processEvent(event);}, true);
	    return heatmapLayer;

	},
	getClassifications: function(heatmap)
	{
	    flattenedValues = flattenValues(heatmap);
            series = new geostats(flattenedValues);

            jenksClassifications = series.getClassJenks(5);
	    return jenksClassifications;
	},

	getColorGradient: function(classifications)
	{
            colors = [0x00000000, 0xfef0d9ff, 0xfdcc8aff, 0xfc8d59ff, 0xe34a33ff, 0xb30000ff];
            colorGradient = {};
            for (var i = 0 ; i < classifications.length ; i++)
	    {
		value = classifications[i];
		scaledValue = rescaleHeatmapValue2(value, jenksClassifications[0], maxValue);
		if (scaledValue < 0)
		    scaledValue = 0;
		colorGradient[scaledValue] = colors[i];
	    }
	    return colorGradient;
	},
	rescaleHeatmaValue: function(value, min, max)
	{
	    if (value == null)
		return 0;
	    if (value == -1)
		return -1;
	    if (value == 0)
		return 0;
	    value = value * 1.0;
	    return (value * 1.0) / max;
	},

	drawHeatmapOpenLayers: function(that, heatmapObject)
	{
	    lastHeatmapObject = heatmapObject;
	    that.deleteHeatmapLayer(that);
	    that.initBackgroundLayer(that);
	    that.heatmapLayer = that.initHeatmapLayer();
	    that.heatmapLayer.points = [];  //delete any previously added points
	    // get components returned by Solr
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

	    var classifications = that.getClassifications(heatmap);
	    var colrGradient = that.getColorGradient(classifications);
	    that.heatmapLayer.setGradientStops(colorGradient);

	    scaledValues = [];
	    clippedValues= [];
	    var radiusFactor = .9;
	    
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
			scaledValue = rescaleHeatmapValue(heatmapValue, classifications[1], maxValue);
			if (heatmapValue > 0)
			{
			    heatmapLayer.addSource(new Heatmap.Source(mercator, radius*radiusFactor, scaledValue));
			    scaledValues.push(scaledValue);
			}
		    }
		    catch (error)
		    {
			console.log("error making heatmap: " + error);
		    }
		}
	    }
	    that.heatmapLayer.setOpacity(0.50);
	    OpenGeoportal.ogp.map.addLayer(that.heatmapLayer);
	    console.log("heatmap displayed.");
	}
    }

);


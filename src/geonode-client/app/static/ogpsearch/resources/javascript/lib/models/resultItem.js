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
			if (typeof heatmapLayer != 'undefined')
			    {
				console.log("removing layer");
				OpenGeoportal.ogp.map.removeLayer(heatmapLayer);
			    }
			tempResponse = dataObj;
			facetCounts = tempResponse.facet_counts;
			facetHeatmaps = facetCounts.facet_heatmaps;
			bbox_rpt = facetHeatmaps.bbox_rpt;
			heatmapPng = bbox_rpt[15];
			// create Image object to get png width and height
			// layer creation based on
			//   http://gis.stackexchange.com/questions/58607/displaying-a-multi-zoom-image-layer-in-open
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

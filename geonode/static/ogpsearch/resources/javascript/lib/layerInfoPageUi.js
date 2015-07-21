
if (typeof OpenGeoportal === 'undefined') {
	OpenGeoportal = {};
} else if (typeof OpenGeoportal !== "object") {
	throw new Error("OpenGeoportal already exists and is not an object");
}

/**
 * LayerInfoPageUi: handle redirect to the the layer info page
 *   this code replaces the metadata handler, hence the function name
 * @requires OpenGeoportal.Template
 */
OpenGeoportal.LayerInfoPageUi = function LayerInfoPageUi() {
	/*
	 * LayerInfoPageUi control
	 * 
	 */
	this.template = OpenGeoportal.ogp.template;

	/*
	 * don't view metadata but send user to layer info page
	 * 
	 */

	this.viewMetadata = function(model) {
	    console.log("in layerInfoPageUi.viewMetadata");
	    layerInfoPage = model.get("Location").layerInfoPage;
	    url = window.location.origin + layerInfoPage;
	    window.location = url;

	}
}
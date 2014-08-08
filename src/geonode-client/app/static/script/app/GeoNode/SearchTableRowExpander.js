Ext.namespace("GeoNode");

GeoNode.SearchTableRowExpander = Ext.extend(Ext.grid.RowExpander, {
    errorText: 'UT: Unable to fetch layer details.',
    loadingText: 'UT: Loading...',
    categoryText: "UT:Category:",
    categoryEmptyText: "UT:No category is provided for this layer.",
    abstractText: "UT:Abstract:",
    attributionEmptyText: "UT: No attribution information is provided for this layer.",
    attributionText: "UT:Provided by:",
    downloadText : "UT:Download:",
    keywordEmptyText: "UT: No keywords are listed for this layer.",
    keywordText: "UT:Keywords:",
    metadataEmptyText: 'UT: No metadata URLs are defined for this layer.',
    metadataText: "UT:Metadata Links:",


    constructor: function(config) {
        //this.fetchURL = config.fetchURL; 
        GeoNode.SearchTableRowExpander.superclass.constructor.call(this, config);
    },

    getRowClass : function(record, rowIndex, p, ds){
        p.cols = p.cols-1;
        return this.state[record.id] ? 'x-grid3-row-expanded' : 'x-grid3-row-collapsed';
    },

    fetchBodyContent: function(body, record, index) {
        if(!this.enableCaching){
            this._fetchBodyContent(body, record, index);
        }
        var content = this.bodyContent[record.id];
        if(!content){
            this._fetchBodyContent(body, record, index);
        }
        else {
            body.innerHTML = content;
        }
    },

    _fetchBodyContent: function(body, record, index) {
        body.innerHTML = this.loadingText;
        detailsTemplate =  new Ext.Template(
            '<p><b>' + this.categoryText + '</b> {category}</p>' +
                '<p><b>' + this.abstractText + '</b> {abstract}</p>' +
                '<p><b>' + this.keywordText + '</b> {keywords}</p>'
        );
        detailsTemplate.overwrite(body, record.data);
        this.bodyContent[record.id] = body.innerHTML;

    },

    beforeExpand : function(record, body, rowIndex){
        if(this.fireEvent('beforeexpand', this, record, body, rowIndex) !== false){
            this.fetchBodyContent(body, record, rowIndex);
            return true;
        }else{
            return false;
        }
    }
});

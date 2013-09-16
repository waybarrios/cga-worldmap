/*globals define: true, requirejs: true */

requirejs.config({
    baseUrl: '/static/lib/js',
    shim: {
        'underscore': { exports: '_'}
    },
    paths: {
        'upload': '../../geonode/js/upload',
        'templates': '../../geonode/js/templates',
    }
});

define(['upload/upload'], function (upload) {
    'use strict';

    $(function () {
        upload.initialize({
            form: '#file-uploader',
            dropZone: '#drop-zone',
            file_queue: '#file-queue',
            clear_button: '#clear-button',
            upload_button: '#upload-button'
        });
        
//        upload.on("initialize", function(){
//            LayerInfo.prototype.displayUploadedLayerLinks = function(resp) {
//            	window.location.href = resp.url + '/metadata';
//            };        	
//        });

        
    });
});

var wtf = define;
var wtf2 = define.LayerInfo;
define = function(){ 
    wtf.apply(null, 
//          LayerInfo.prototype.displayUploadedLayerLinks = function(resp) {
//        	window.location.href = resp.url + '/metadata';
//        }; 		
    ); 
}

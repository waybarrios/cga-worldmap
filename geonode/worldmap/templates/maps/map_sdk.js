{% include 'geonode/ext_header.html' %}
{% include 'geonode/sdk_header.html' %}
<style type="text/css">
#aboutbutton {
    display: none;
}
#paneltbar {
    margin-top: 90px;
}
button.logout {
    display: none;
}
button.login {
    display:none;
}
.map-title-header {
    margin-right: 10px;
}
</style>
<script type="text/javascript">
var app;
Ext.onReady(function() {
{% autoescape off %}
    var config = Ext.apply({
        authStatus: {% if user.is_authenticated %} 200{% else %} 401{% endif %},
        proxy: "/proxy/?url=",
        printService: "{{GEOSERVER_BASE_URL}}pdf/",
        /* The URL to a REST map configuration service.  This service 
         * provides listing and, with an authenticated user, saving of 
         * maps on the server for sharing and editing.
         */
        rest: "/maps/",
        ajaxLoginUrl: "{% url "account_ajax_login" %}",
        homeUrl: "{% url "home" %}",
        localGeoServerBaseUrl: "{{ GEOSERVER_BASE_URL }}",
        localCSWBaseUrl: "{{ CATALOGUE_BASE_URL }}",
        csrfToken: "{{ csrf_token }}"
    }, {{ config }});


    app = new GeoNode.Composer(config);
{% endautoescape %}
});
</script>
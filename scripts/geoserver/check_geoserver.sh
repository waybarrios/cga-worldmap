#!/bin/bash

# this script must be scheduled at the same time as the authorization check script

for instance in tomcata tomcatb; do

    echo "Checking $instance"

    if [ $instance = "tomcata" ]
    then
        port=8180
    else
        port=8280
    fi

    url="http://localhost:$port/geoserver/wms?STYLES=&FORMAT=image%2Fpng&TRANSPARENT=TRUE&LAYERS=geonode%3ADE01_SL6_22P_1T_20100521T010517_20100521T010602_DMI_0_1b5d_qXM&EXCEPTIONS=application%2Fvnd.ogc.se_inimage&VERSION=1.1.1&SERVICE=WMS&REQUEST=GetMap&LLBBOX=137.36632816178096,36.772883864884584,141.8751878470843,40.26195796778519&URL=http%3A%2F%2Flocalhost%3A8180%2Fgeoserver%2Fwms&TILED=true&TILESORIGIN=15291549.700982,4407496.8300991&SRS=EPSG%3A900913&BBOX=15654303.390625,4657155.2587109,15693439.149102,4696291.0171875&WIDTH=256&HEIGHT=256"

    echo "Checking url $url"
    curl $url --connect-timeout 5 --max-time 20 -s -f -o /dev/null

    if [ $? -eq 0 ]
    then
            echo "GeoServer running on $instance is doing well :)"
    else
            /usr/bin/curl -X POST \
            -s \
              --data-urlencode "payload={ \
            \"channel\": \"#worldmap-log\", \
            \"username\": \"Cron\", \
            \"pretext\": \"wm-java-primary\", \
            \"color\": \"danger\", \
            \"icon_emoji\": \":ghost:\", \
            \"text\": \"Tiles not being rendered, restarting Tomcat a\" \
            }" \
            https://hooks.slack.com/services/xxxxx/yyyyy/zzzzz
            echo "Restarting $instance"
            sudo service $instance stop
    fi
done

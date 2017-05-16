#!/bin/bash

RANDOM=$((1 + RANDOM % 1000))
URL="http://worldmap.harvard.edu/geonetwork/srv/en/main.search.embedded?any=lakes&sortBy=relevance&hitsPerPage=10&output=full&fake=$RANDOM"
echo $URL
STATUS=`wget --spider -S "$URL" 2>&1 | grep "HTTP/" | awk '{print $2}'`
echo $STATUS

must_restart=false
if [ "$STATUS" -eq 200 ];then
    echo "GeoNetwork is running"
else
    echo "Must restart GeoNetwork"
    must_restart=true
fi

if $must_restart ; then
    echo $(date)
    echo "Going to restart GeoNetwork"
    /usr/bin/curl -X POST \
        -s \
          --data-urlencode "payload={ \
        \"channel\": \"#worldmap-log\", \
        \"username\": \"Cron\", \
        \"pretext\": \"geonetwork-failure\", \
        \"color\": \"danger\", \
        \"icon_emoji\": \":imp:\", \
        \"text\": \"Restarting GeoNetwork \" \
    }" \
    https://hooks.slack.com/services/xxxxx/yyyyy/zzzzz
    service tomcatc stop
fi

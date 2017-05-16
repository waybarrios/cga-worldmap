#!/bin/bash

# this is to avoid issue #95. It should not be needed anymore when we move to GeoNode 2.6 (GeoServer 2.8)

layer=$(sudo grep -i "Caused by: java.lang.IllegalArgumentException: value already present"  /opt/tomcat/a/logs/catalina.out | tail -1 | sed -n 's/.* //p' | tr -d '\012\015' | awk '{print $NF}')
echo $layer

if [ ! -z "$layer" ]
then
  cd /mnt/sdp/opt/geonode/data/gwc-layers/
  result=$(grep -r -l -i "$layer")
  echo "$result"
  if [ ! -z "$result" ];
  then
    echo "$layer has duplicated cache, going to remove it."
    #echo $result | xargs ls -lh
    echo $result | xargs rm -fr
    /usr/bin/curl \
        -X POST \
        -s \
          --data-urlencode "payload={ \
        \"channel\": \"#worldmap-log\", \
        \"username\": \"Monit\", \
        \"pretext\": \"wm-java\", \
        \"color\": \"danger\", \
        \"icon_emoji\": \":thunder_cloud_and_rain:\", \
        \"text\": \"Found layer with duplicated cache. Fixing cache and restarting Tomcat\" \
    }" \
    https://hooks.slack.com/services/xxxxx/yyyyy/zzzzz
    # uncomment to restart Tomcat
    echo 'Restarting tomcata'
    sudo service tomcata stop
    sleep 600s
    echo 'Restarting tomcatb'
    sudo service tomcatb stop
  fi
else
    echo 'Cache is in good conditions :)'
fi

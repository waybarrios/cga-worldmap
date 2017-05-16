#!/bin/bash

cd /home/ubuntu/scripts/

auth_is_ok=$(/usr/bin/python /home/ubuntu/scripts/check_auth.py)
echo Is GeoNode auth working properly? $auth_is_ok

if [ $auth_is_ok = "False" ]; then
        /usr/bin/curl \
        -X POST \
        -s \
          --data-urlencode "payload={ \
        \"channel\": \"#worldmap-log\", \
        \"username\": \"Monit\", \
        \"pretext\": \"wm-java\", \
        \"color\": \"danger\", \
        \"icon_emoji\": \":scream_cat:\", \
        \"text\": \"Security system corrupted, restarting Tomcat\" \
    }" \
    https://hooks.slack.com/services/xxxxx/yyyyy/zzzzz

    echo restarting tomcat
    sudo /usr/bin/service tomcata stop
fi

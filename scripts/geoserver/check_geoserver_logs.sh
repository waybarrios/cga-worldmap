#!/bin/bash
#error=`cat /tmp/gntest.txt`

for tc_instance in 'a' 'b'
do

        last10K=`tail -n 10000 /opt/tomcat/$tc_instance/logs/catalina.*`
        time=`date +"%m-%d-%y-%H-%M"`
        ex2='at org.geoserver.catalog.impl.DefaultCatalogFacade.get'
        ex1='NulllPointerException'
        ex3='Error getting FeatureType, this should never happen'
        ex4='java.rmi.server.ExportException: Port already in use:'
        ex5='Error occured on rollback'
        ex6='Error occurred creating table'

        #if [[ $last10K =~ $ex4 || $last10K =~ $ex5 ]]; then
        if [[ $last10K =~ $ex5 || $last10K =~ $ex6 ]]; then
                echo "ERROR"
                echo 'error' > /tmp/gntest.txt
                export MONIT_DESCRIPTION="Stopping Tomcat $tc_instance - Dupe or DB Error on WorldMap"
                export MONIT_DATE="$time"
                sh /root/scripts/slack_notifications.sh
                mkdir -p /tmp/tomcata-failed-$MONIT_DATE
                mv -f /opt/tomcat/$tc_instance/logs/* /tmp/tomcata-failed-$MONIT_DATE
                service tomcat$tc_instance stop
        fi

        #If there is the infamous catalog exception in the log, restart Tomcat
        if [[ $last10K =~ $ex1 ]]; then
                if [[ $last10K =~ $ex2  ]];     then
                        echo 'error' > /tmp/gntest.txt
                        export MONIT_DESCRIPTION="Stopping Tomcat $tc_instance - Catalog Error on WorldMap"
                        export MONIT_DATE="$time"
                        sh /root/scripts/slack_notifications.sh
                        mkdir -p /tmp/tomcata-failed-$MONIT_DATE
                        mv -f /opt/tomcat/$tc_instance/* /tmp/tomcata-failed-$MONIT_DATE

                        service tomcat$tc_instance stop
                fi
        fi
done

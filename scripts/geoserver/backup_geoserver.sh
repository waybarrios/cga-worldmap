cd /mnt/sdp/backup/geoserver
rm *.tar.gz
geoserver_data_dir=/mnt/sdp/opt/geonode/data
today=$(date +"%Y%m%d")
tar -zcvf $today.tar.gz $geoserver_data_dir
s3cmd put $today.tar.gz s3://wm-geoserver-backup

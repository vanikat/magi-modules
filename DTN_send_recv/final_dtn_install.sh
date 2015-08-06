#!/bin/bash

#bootstraping MAGI
sudo python /share/magi/current/magi_bootstrap.py

#installing dependencies for DTN
sudo apt-get -y install libxerces-c2-dev
sudo apt-get -y install libxerces-c28
sudo apt-get -y install libxerces-c3.1
sudo apt-get -y install libxerces2-java
sudo /share/magi/dev/source/berkely-db.install /tmp /share/magi/dev/source
sudo /share/magi/dev/source/tcl-old.install /tmp /share/magi/dev/source
sudo /share/magi/dev/source/oasys-old.install /tmp /share/magi/dev/source

#installing DTN
sudo /share/magi/dev/source/dtn.install /tmp /share/magi/dev/source

short_hostname="$(echo $HOSTNAME| cut -d"." -f1)"
configfile="/proj/montage/magi-modules/DTN_send_recv/conf_files/"$short_hostname"_dtn.conf"

#instantiating DTN
sudo dtnd -c $configfile --init-db
sudo dtnd -c $configfile -o /home/user/dtn/dtnd.log -d 

#!/bin/sh

sudo route del -net node-0-link0 netmask 255.255.255.255
sudo route add -net node-0-link0 netmask 255.255.255.255 gw control
sudo route del -net node-1-link1 netmask 255.255.255.255
sudo route add -net node-1-link1 netmask 255.255.255.255 gw control
sudo route del -net node-2-link2 netmask 255.255.255.255
sudo route add -net node-2-link2 netmask 255.255.255.255 gw control
sudo route del -net node-3-link3 netmask 255.255.255.255
sudo route add -net node-3-link3 netmask 255.255.255.255 gw control
sudo route del -net node-4-link4 netmask 255.255.255.255
sudo route add -net node-4-link4 netmask 255.255.255.255 gw control

sudo route del -net node-0-link0b netmask 255.255.255.255
sudo route add -net node-0-link0b netmask 255.255.255.255 gw controlb
sudo route del -net node-1-link1b netmask 255.255.255.255
sudo route add -net node-1-link1b netmask 255.255.255.255 gw controlb
sudo route del -net node-2-link2b netmask 255.255.255.255
sudo route add -net node-2-link2b netmask 255.255.255.255 gw controlb
sudo route del -net node-3-link3b netmask 255.255.255.255
sudo route add -net node-3-link3b netmask 255.255.255.255 gw controlb
sudo route del -net node-4-link4b netmask 255.255.255.255
sudo route add -net node-4-link4b netmask 255.255.255.255 gw controlb

exit 0

#!/bin/sh

apt-get update
apt-get install rsnapshot -y

<<DOC
To reset ssh-config with odoo machine:
sudo ssh-keygen -f "/root/.ssh/known_hosts" -R 192.168.50.4
sudo ssh-copy-id -i /root/.ssh/id_rsa.pub vagrant@192.168.50.4

To fetch remote specific database:
sudo ssh vagrant@192.168.50.4 pg_dump testBase

To test rsnapshop configuration and backup:
sudo rsnapshot configtest
sudo rsnapshot hourly
DOC
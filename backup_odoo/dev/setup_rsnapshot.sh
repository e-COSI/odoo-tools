#!/bin/sh

apt-get update
apt-get install -y rsnapshot
apt-get install -y postgresql-client-9.6

<<DOC
sudo ssh-keygen -t rsa
To reset ssh-config with odoo machine:
sudo ssh-keygen -f "/root/.ssh/known_hosts" -R 192.168.50.4
sudo ssh-copy-id -i /root/.ssh/id_rsa.pub vagrant@192.168.50.4

To test rsnapshop configuration and backup:
sudo rsnapshot configtest
sudo rsnapshot hourly
DOC
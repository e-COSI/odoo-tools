#!/bin/sh

apt-get update
apt-get install rsnapshot -y

<<DOC
To fetch remote specific database:
sudo ssh vagrant@192.168.50.4 pg_dump testBase

To test rsnapshop configuration and backup:
sudo rsnapshot configtest
sudo rsnapshot hourly
DOC
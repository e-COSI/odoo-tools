#!/bin/bash

apt-get update

# NGINX
apt-get install -y nginx
# Allow nginx communication on port 80
ufw allow 'Nginx HTTP'

# MUNIN
apt-get -y install munin munin-node munin-plugins-extra
ln -s /var/cache/munin/www /usr/share/nginx/html/munin

/etc/init.d/munin-node restart
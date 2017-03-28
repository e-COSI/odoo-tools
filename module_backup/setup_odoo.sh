#!/bin/sh

apt-get update
cd /home/vagrant
wget https://raw.githubusercontent.com/Yenthe666/InstallScript/10.0/odoo_install.sh
chmod +x odoo_install.sh
./odoo_install.sh

sudo -u postgres psql -c <<PG_CONFIG
CREATE USER vagrant WITH PASSWORD vagrant;
ALTER USER vagrant WITH SUPERUSER;
PG_CONFIG

<<COMMENT
sudo su -postgres
createuser -sPE vagrant
PG_CONFIG
COMMENT

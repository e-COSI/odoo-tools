#!/bin/sh

apt-get update
cd /home/vagrant
wget https://raw.githubusercontent.com/Yenthe666/InstallScript/10.0/odoo_install.sh
chmod +x odoo_install.sh
./odoo_install.sh

sudo -u postgres psql -c "createuser -sPE vagrant"

<<PG_CONFIG
CREATE USER vagrant WITH PASSWORD vagrant;
ALTER USER vagrant WITH SUPERUSER;
PG_CONFIG

cat >> /home/vagrant/.bashrc <<BASH_CONFIG

config_path=/home/vagrant/SharedFolder/.config_sh
if [ -x \$config_path ]; then
    source \$config_path
fi
BASH_CONFIG

<<COMMENT
sudo su postgres
createuser -sPE vagrant
PG_CONFIG
COMMENT

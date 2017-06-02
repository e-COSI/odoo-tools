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

If remote postresql-client cannot connect to local psql-server
    -> ERROR (Is the server running on host "xx.xx.xx.xx" and accepting TCP/IP connections on port 5432?)

    => Edit /etc/postgresql/{version}/main/postgresql.conf
        listen_addresses = '*'

    => Edit /etc/postgresql/{version}/main/pg_hba.conf
        host    all             all             192.168.1.0/24          md5

COMMENT

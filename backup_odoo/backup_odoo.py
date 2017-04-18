#!/usr/bin/python

from sys import argv
from os import path
import os, sys, io
import logging, json, argparse

from time import time

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("SNAPSHOT_CONF")
VERSION = "1.0.0"


class BackupOdooParser(argparse.ArgumentParser):
    """
    Personalized error messages for ArgumentParser.
    """

    def error(self, message):
        self.print_usage()
        sys.stderr.write("error: %s\n" % message)
        sys.exit(2)


class BackupOdoo(object):
    """
    Backup Odoo manager
    """

    def __init__(self):
        """
        Class constructor initializing command line options.
        """
        parser = BackupOdooParser()
        parser.add_argument("--config", "-c", help="specify json config file")
        parser.add_argument("--databases", "-d", help="filter database to process")
        parser.add_argument("--filestore", "-F", action="store_true", default=False)
        parser.add_argument("--postgres", "-P", action="store_true", default=False)
        parser.add_argument("--restore", "-r", action="store_true",
                            help="restore backup data", default=False)
        parser.add_argument("--zip", "-z", help="compress last available backup")
        parser.add_argument("--version", "-v", action="store_true")

        self.parser = parser
        self.data = {}
        self.args = parser.parse_args()

    def run(self):
        """
        Launch backup script operations.
        """
        if not self.args.config:
            self.parser.error("argument --config/-c is required")
        if self.args.filestore and self.args.postgres:
            self.parser.error("cannot specify filesore and postgres arguments at the same time")
        with open(self.args.config, 'r') as data_file:
            self.data = json.load(data_file)
            if not self.args.postgres:
                self.handle_filestore()
            if not self.args.filestore:
                self.handle_database()

    def handle_filestore(self):
        """
        Main Odoo filestore handler: format backup lines that will be inserted in rsnapshot
        config file template if in backup mode, otherwise format command line used
        to restore most recent local saved filestore to remote target.
        """
        backup_lines = []
        filter_db = self.args.databases.split(",") if self.args.databases else []
        for db in self.data["databases"]:
            for name in [n for n in db["db_names"] if n not in filter_db]:
                fs_path = path.join(db["filestore_path"], name)
                line = ""
                if self.args.restore:
                    line = self._prepare_restore_command_line(db, name)
                else:
                    # Format filestore backup line for snapshot config file
                    line = "backup {0}:{1} {2}".format(db["base_url"], fs_path, db["source"])
                backup_lines.append(line)
        try:
            if self.args.restore:
                _logger.info("Restoring filestore...")
                cmd = "\n".join(backup_lines)
            else:
                _logger.info("Backing up filestore...")
                cmd = self._generate_snapshot_command(backup_lines)
            _logger.debug("Running command: " + cmd)
            os.system(cmd)
        except Exception as e:
            _logger.exception(e)

    def handle_database(self):
        """
        Main postgres database handler: format command line to either restore lastest
        saved local dump to remove database or to create new backup of remote database.
        """
        filter_db = self.args.databases.split(",") if self.args.databases else []
        for db in self.data["databases"]:
            for name in [n for n in db["db_names"] if n not in filter_db]:
                db_path = path.join(self.data["backup_root"] + "db", db["source"])
                try:
                    if not path.exists(db_path):
                        os.makedirs(db_path)
                    pg_dumps = sorted(os.listdir(db_path))
                    msg = "Dumps available for {0}: {1}".format(name, pg_dumps)
                    _logger.debug(msg)
                    db_path = path.join(self.data["backup_root"] + "db", db["source"])
                    cmd = ""
                    if self.args.restore:
                        # Check if there is at least one file to restore
                        if len(pg_dumps) == 0:
                            _logger.error("No postgres dump available to restore " + name)
                            continue
                        _logger.info("Restoring databases...")
                        # Select most recent available postgres dump to restore it
                        dump_id = pg_dumps[-1]
                        cmd = self._format_postgres_restore(db["base_url"], name, db_path, dump_id)
                    else:
                        _logger.info("Backing up databases...")
                        cmd = self._format_postgres_dump(db["base_url"], name, db_path, pg_dumps)
                    _logger.debug("Running command: " + cmd)
                    os.system(cmd)
                except Exception as e:
                    _logger.exception(e)

    def _prepare_restore_command_line(self, db, name):
        """
        Helper method used to create formated command line used to restore remote filestore
        using rsync.
        """
        fs_path = db["filestore_path"] + name + "/"
        backup_path = "{0}filestore/hourly.0/{1}" \
            .format(self.data["backup_root"], db["source"])
        return "rsync -av {local_path}{filestore} {source_url}:{filestore}".format(
            filestore=fs_path,
            local_path=backup_path,
            source_url=db["base_url"]
        )

    def _generate_snapshot_command(self, backup_lines):
        """
        Helper method used to create formatted rsnapshot config file used to backup remote
        Odoo filestore.
        """
        conf_file = self.data["conf_path"]
        with open("rsnapshot/template.conf", 'r') as conf:
            file_content = conf.read().format(
                root=self.data["backup_root"] + "filestore/",
                backups="\n".join(backup_lines)
            ).replace(" ", "\t") \
            .replace('\r\n', '\n').replace('\r', '\n')
            with open(conf_file, 'w') as f:
                f.write(file_content)
                _logger.info("Configuration file written to: " + conf_file)
            return "rsnapshot -c {} hourly".format(conf_file)

    def _format_postgres_dump(self, url, database, db_path, pg_dumps):
        """
        Helper method used to create formated command line used to dump postgres database.
        """
        # Create pg database dump with timestamp id name
        dump_id = "{0}_{1}.gz".format(database, int(time()))
        # Filter the 4 oldest database dumps
        old_dumps = pg_dumps[:-4]
        msg = "Old pg dumps to remove: {}".format(old_dumps)
        _logger.debug(msg)
        for d in old_dumps:
            os.remove(path.join(db_path, d))
        # Dump database to output and compress it before saving it
        return "ssh {source_url} pg_dump {db_name} | gzip > {dest_file}".format(
            source_url=url,
            db_name=database,
            dest_file=path.join(db_path, dump_id)
        )

    def _format_postgres_restore(self, url, database, db_path, dump_id):
        """
        Helper method used to create formated command line used to restore postgres database.
        """
        return """
        ssh {source_url} dropdb {db_name}
        scp {local_file} {source_url}:{temp_file} &&
        ssh {source_url} createdb {db_name} &&
        #ssh {source_url} 'psql {db_name} < {temp_file}'
        ssh {source_url} 'gunzip -c {temp_file} | psql {db_name} > /dev/null'
        """.format(
            local_file=path.join(db_path, dump_id),
            temp_file="/tmp/" + dump_id,
            source_url=url,
            db_name=database
        )

try:
    backup_handler = BackupOdoo()
    if backup_handler.args.version:
        print "Backup Odoo version: " + VERSION
    else:
        backup_handler.run()
except Exception as e:
    _logger.exception(e)

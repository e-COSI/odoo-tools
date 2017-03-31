#!/usr/bin/python

from sys import argv
from os import path
import os
import logging, json, argparse

from time import time

logging.basicConfig(level=logging.DEBUG)
_logger = logging.getLogger("SNAPSHOT_CONF")

parser = argparse.ArgumentParser()
#parser.add_argument("--backup", "-b", help="launch backup operation with rsnapshot config")
parser.add_argument("--config", "-c", help="specify json config file", required=True)
parser.add_argument("--databases", "-d", help="filter database to process")
parser.add_argument("--filestore", "-FS", action="store_true")
parser.add_argument("--postgres", "-PG", action="store_true")
parser.add_argument("--restore", "-r", action="store_true", help="restore backup data", default=False)
parser.add_argument("--zip", "-z", help="compress last available backup")
args = parser.parse_args()

def generate_snapshot(args, data):
    backup_lines = []
    filter_db = args.databases.split(",") if args.databases else []
    for db in data["databases"]:
        for name in [n for n in db["db_names"] if n not in filter_db]:
            fs_path = path.join(db["filestore_path"], name)
            line = ""
            if args.restore:
                fs_path = db["filestore_path"] + name + "/"
                backup_path = "{0}filestore/hourly.0/{1}" \
                    .format(data["backup_root"], db["source"])
                line = "rsync -av {local_path}{filestore} {source_url}:{filestore}".format(
                    filestore=fs_path,
                    local_path=backup_path,
                    source_url=db["base_url"]
                )
            else:
                line = "backup {0}:{1} {2}".format(db["base_url"], fs_path, db["source"])
            backup_lines.append(line)

    try:
        if args.restore:
            cmd = "\n".join(backup_lines)
        else:
            conf_file = data["conf_path"]
            with open("rsnapshot/template.conf", 'r') as conf:
                file_content = conf.read().format(
                    root=data["backup_root"] + "filestore/",
                    backups="\n".join(backup_lines)
                ).replace(" ", "\t")
                with open(conf_file, 'w') as f:
                    f.write(file_content)
                    _logger.info("Configuration file written to: " + conf_file)
                cmd = "rsnapshot -c {} hourly".format(conf_file)
        _logger.info("Running command: " + cmd)
        os.system(cmd)
    except Exception as e:
        _logger.exception(e)

def generate_postgres_dump(args, data):
    filter_db = args.databases.split(",") if args.databases else []
    for db in data["databases"]:
        for name in [n for n in db["db_names"] if n not in filter_db]:
            db_path = path.join(data["backup_root"] + "db", db["source"])
            try:
                if not path.exists(db_path):
                    os.makedirs(db_path)
                pg_dumps = sorted(os.listdir(db_path))
                msg = "Dumps available for {0}: {1}".format(name, pg_dumps)
                _logger.debug(msg)
                db_path = path.join(data["backup_root"] + "db", db["source"])
                cmd = ""
                if args.restore:
                    # CHeck there is at least one file to restore
                    if len(pg_dumps) == 0:
                        _logger.error("No postgres dump available to restore " + name)
                        continue
                    dump_id = pg_dumps[-1]
                    cmd = """
                    ssh {source_url} dropdb {db_name}
                    scp {local_file} {source_url}:{temp_file} &&
                    ssh {source_url} createdb {db_name} &&
                    #ssh {source_url} 'psql {db_name} < {temp_file}'
                    ssh {source_url} 'gunzip -c {temp_file} | psql {db_name} > /dev/null'
                    """.format(
                        local_file=path.join(db_path, dump_id),
                        temp_file="/tmp/" + dump_id,
                        source_url=db["base_url"],
                        db_name=name
                    )
                else:
                    # Create pg database dump with timestamp id name
                    dump_id = "{0}_{1}.gz".format(name, int(time()))
                    old_dumps = pg_dumps[:-4]
                    msg = "Old pg dumps to remove: {}".format(old_dumps)
                    _logger.debug(msg)
                    for d in old_dumps:
                        os.remove(path.join(db_path, d))
                    # Dump database to output and compress it before saving it
                    cmd = "ssh {source_url} pg_dump {db_name} | gzip > {dest_file}".format(
                        source_url=db["base_url"],
                        db_name=name,
                        dest_file=path.join(db_path, dump_id)
                    )
                _logger.info("Running command: " + cmd)
                os.system(cmd)
            except Exception as e:
                _logger.exception(e)

try:
    assert not (args.filestore and args.postgres)
    with open(args.config, 'r') as data_file:
        data = json.load(data_file)
        if not args.postgres:
            generate_snapshot(args, data)
        if not args.filestore:
            generate_postgres_dump(args, data)
except Exception as e:
    _logger.exception(e)

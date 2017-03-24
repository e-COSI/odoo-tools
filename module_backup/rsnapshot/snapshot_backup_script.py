#!/usr/bin/python

from sys import argv
#from os.path import isfile, join, exists
#from os import listdir, makedirs, system
from os import path
import os
import logging, json, argparse

from time import time


SNAPSHOT_CONF = """
#################################################
# rsnapshot.conf - rsnapshot configuration file #
#################################################
#											   #
# PLEASE BE AWARE OF THE FOLLOWING RULES:	   #
#											   #
# This file requires tabs between elements	  #
#											   #
# Directories require a trailing slash:		 #
#   right: /home/							   #
#   wrong: /home								#
#											   #
#################################################

#######################
# CONFIG FILE VERSION #
#######################

config_version	1.2

###########################
# SNAPSHOT ROOT DIRECTORY #
###########################

# All snapshots will be stored under this root directory.
#
snapshot_root	{root}

# If no_create_root is enabled, rsnapshot will not automatically create the
# snapshot_root directory. This is particularly useful if you are backing
# up to removable media, such as a FireWire or USB drive.
#
#no_create_root	1

#################################
# EXTERNAL PROGRAM DEPENDENCIES #
#################################

# LINUX USERS:   Be sure to uncomment "cmd_cp". This gives you extra features.
# EVERYONE ELSE: Leave "cmd_cp" commented out for compatibility.
#
# See the README file or the man page for more details.
#
cmd_cp		/bin/cp

# uncomment this to use the rm program instead of the built-in perl routine.
#
cmd_rm		/bin/rm

# rsync must be enabled for anything to work. This is the only command that
# must be enabled.
#
cmd_rsync	/usr/bin/rsync

# Uncomment this to enable remote ssh backups over rsync.
#
cmd_ssh	/usr/bin/ssh

# Comment this out to disable syslog support.
#
cmd_logger	/usr/bin/logger

# Uncomment this to specify the path to "du" for disk usage checks.
# If you have an older version of "du", you may also want to check the
# "du_args" parameter below.
#
cmd_du		/usr/bin/du

# Uncomment this to specify the path to rsnapshot-diff.
#
#cmd_rsnapshot_diff	/usr/bin/rsnapshot-diff

#########################################
#		   BACKUP INTERVALS			#
# Must be unique and in ascending order #
# i.e. hourly, daily, weekly, etc.	  #
#########################################

retain		hourly	6
retain		daily	7
retain		weekly	4
#retain	monthly	3

############################################
#			  GLOBAL OPTIONS			  #
# All are optional, with sensible defaults #
############################################

# Verbose level, 1 through 5.
# 1	 Quiet		   Print fatal errors only
# 2	 Default		 Print errors and warnings only
# 3	 Verbose		 Show equivalent shell commands being executed
# 4	 Extra Verbose   Show extra verbose information
# 5	 Debug mode	  Everything
#
verbose		2

# Same as "verbose" above, but controls the amount of data sent to the
# logfile, if one is being used. The default is 3.
#
loglevel	3

# If you enable this, data will be written to the file you specify. The
# amount of data written is controlled by the "loglevel" parameter.
#
#logfile	/var/log/rsnapshot.log

# If enabled, rsnapshot will write a lockfile to prevent two instances
# from running simultaneously (and messing up the snapshot_root).
# If you enable this, make sure the lockfile directory is not world
# writable. Otherwise anyone can prevent the program from running.
#
lockfile	/var/run/rsnapshot.pid

# By default, rsnapshot check lockfile, check if PID is running
# and if not, consider lockfile as stale, then start
# Enabling this stop rsnapshot if PID in lockfile is not running
#
#stop_on_stale_lockfile		0

###############################
### BACKUP POINTS / SCRIPTS ###
###############################

# LOCALHOST
{backups}
"""

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
			file_content = SNAPSHOT_CONF.format(
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

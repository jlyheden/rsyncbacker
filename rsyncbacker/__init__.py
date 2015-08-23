from rsyncbacker.exception import ConfigurationException, BackupExecutionException
from rsyncbacker.util import get_ipv4_addresses_on_host, is_host_on_lan

import logging
import subprocess

LOGGER = logging.getLogger(__name__)


class RsyncExecutor(object):

    def __init__(self):
        self.target_host = None
        self.target_rsync_name = None
        self.target_rsync_path = None
        self.target_rsync_user = None
        self.target_use_ssh = False
        self.target_ssh_key = None
        self.target_ssh_user = None
        self.excludes = []
        self.includes = []
        self.source_path = None
        self.cmd_line = []

    def load_config(self, config):
        try:
            self.target_host = config["target"]["host"]
        except KeyError:
            msg = "Must specify target.host"
            LOGGER.error(msg)
            raise ConfigurationException(msg)

        try:
            self.target_rsync_name = config["target"]["rsync_name"]
        except KeyError:
            try:
                self.target_rsync_path = config["target"]["rsync_path"]
            except KeyError:
                msg = "Neither target.rsync_name or target.rsync_path set"
                LOGGER.error(msg)
                raise ConfigurationException(msg)

        try:
            self.target_rsync_user = config["target"]["rsync"]["user"]
        except KeyError:
            LOGGER.info("No user set in target.rsync_user, will use defaults")

        try:
            self.target_use_ssh = config["target"]["use_ssh"]
            if self.target_use_ssh not in [True, False]:
                raise ConfigurationException("Setting target.use_ssh must be a boolean")
        except KeyError:
            LOGGER.info("No setting for target.use_ssh, using default False")

        if self.target_use_ssh:
            try:
                self.target_ssh_user = config["target"]["ssh_user"]
            except KeyError:
                LOGGER.info("No setting for target.ssh_user, using your currently logged in user")
            try:
                self.target_ssh_key = config["target"]["ssh_key"]
            except KeyError:
                LOGGER.info("No setting for target.ssh_key, taking no responsibility for that setting")

        try:
            self.excludes = config["excludes"]
        except KeyError:
            LOGGER.info("No excludes set in excludes")

        try:
            self.includes = config["includes"]
        except KeyError:
            LOGGER.info("No includes set in includes")

        try:
            self.source_path = config["source"]["path"]
        except KeyError:
            msg = "No source path set in source.path"
            LOGGER.error(msg)
            raise ConfigurationException(msg)

    @staticmethod
    def _cmdline_builder_from_list(argument, collection):
        rv = []
        for item in collection:
            rv.append("%s=%s" % (argument, item))
        return rv

    def should_backup_run(self):
        ifaces = get_ipv4_addresses_on_host()
        return is_host_on_lan(self.target_host, ifaces)

    def commandline_builder(self):
        self.cmd_line = ['/usr/bin/env', 'rsync', '-a', '--delete']
        [self.cmd_line.append(x) for x in self._cmdline_builder_from_list("--exclude", self.excludes)]
        [self.cmd_line.append(x) for x in self._cmdline_builder_from_list("--include", self.includes)]

        if self.target_use_ssh:
            self.cmd_line.append("-e")
            ssh_cmd = "ssh"
            if self.target_ssh_key is not None:
                ssh_cmd = "%s -i %s" % (ssh_cmd, self.target_ssh_key)
            if self.target_ssh_user is not None:
                ssh_cmd = "%s -l %s" % (ssh_cmd, self.target_ssh_user)
            self.cmd_line.append("\"%s\"" % ssh_cmd)

        self.cmd_line.append(self.source_path)

        if self.target_rsync_name is not None:
            destination = "::%s" % self.target_rsync_name
        else:
            destination = ":%s" % self.target_rsync_path

        if self.target_rsync_user is not None:
            destination = "%s@%s%s" % (self.target_rsync_user, self.target_host, destination)
            self.cmd_line.append(destination)
        else:
            destination = "%s%s" % (self.target_host, destination)
            self.cmd_line.append(destination)

    def execute_backup(self):
        proc = subprocess.Popen(self.cmd_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        for line in proc.stdout:
            LOGGER.info(line)
        if proc.returncode != 0:
            raise BackupExecutionException("Backup command failed to execute")


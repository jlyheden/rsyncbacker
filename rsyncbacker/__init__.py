__author__ = 'johan'

import yaml
import logging
import subprocess
import re

LOGGER = logging.getLogger(__name__)


def load_config(yml_file):
    try:
        return yaml.load(open(yml_file).read())
    except IOError, ex:
        LOGGER.error("Failed to load config file %s" % yml_file, ex)


def get_ipv4_addresses_on_host():
    rv = []
    p = subprocess.Popen(['/usr/bin/env', 'ifconfig', '-a'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         shell=False)
    output = p.communicate()
    if p.returncode != 0:
        raise ConfigurationException("Failed to identify my local IP-addresses, output: %s" % output[1])

    pattern = re.compile("^\s+inet ([0-9\.]+) netmask ([0-9]x[0-9a-f]+) broadcast ([0-9\.]+)$")
    for line in output[0].splitlines():
        result = re.match(pattern, line)
        if result:
            rv.append({
                "ip": result.group(1),
                "netmask": result.group(2),
                "broadcast": result.group(3)
            })
    return rv


class ConfigurationException(BaseException):
    pass


class BackupExecutionException(BaseException):
    pass


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
        except KeyError, ex:
            LOGGER.error("Must specify target.host")
            raise ConfigurationException(ex)

        try:
            self.target_rsync_name = config["target"]["rsync_name"]
        except KeyError:
            try:
                self.target_rsync_path = config["target"]["rsync_path"]
            except KeyError, ex:
                LOGGER.error("Neither target.rsync_name or target.rsync_path set")
                raise ConfigurationException(ex)

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
        except KeyError, ex:
            LOGGER.error("No source path set in source.path")
            raise ConfigurationException(ex)

    @staticmethod
    def _cmdline_builder_from_list(argument, collection):
        rv = []
        for item in collection:
            rv.append("%s=%s" % (argument, item))
        return rv

    def should_backup_run(self):
        pass

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


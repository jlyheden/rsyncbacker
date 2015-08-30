from rsyncbacker.exception import ConfigurationException, BackupExecutionException
from rsyncbacker.hdiutil import ImageManager
from rsyncbacker.mount import MountAfp
from rsyncbacker.util import get_ipv4_addresses_on_host, is_host_on_lan

import logging
import subprocess

LOGGER = logging.getLogger(__name__)


class RsyncExecutor(object):

    def __init__(self):
        self.target_host = None
        self.target_share = None
        self.target_username = None
        self.target_password = None
        self.target_passphrase = None
        self.target_image_size = None
        self.target_local_destination = "/Volumes/backupvol"
        self.target_image_loc = None
        self.excludes = []
        self.includes = []
        self.source_path = None
        self.cmd_line = []

        self.mounter = None
        self.backup_image = None

    def load_config(self, config):
        try:
            self.target_host = config["target"]["host"]
            self.target_share = config["target"]["share"]
            self.target_username = config["target"]["username"]
            self.target_password = config["target"]["password"]
            self.target_passphrase = config["target"]["passphrase"]
            self.target_image_size = config["target"]["image_size"]
        except KeyError, ex:
            msg = "Incomplete target configuration %s" % ex.message
            LOGGER.error(msg)
            raise ConfigurationException(msg)

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

        self.mounter = MountAfp(self.target_host, self.target_share, self.target_username, self.target_password)
        self.target_image_loc = "%s/backupvol" % self.mounter.mount_point
        self.backup_image = ImageManager(self.target_passphrase, self.target_image_loc, self.target_local_destination)

    def set_up(self):
        if not self.mounter.is_mounted():
            LOGGER.info("Mounting fileshare on backup server")
            self.mounter.mount()

        if not self.backup_image.image_exists():
            LOGGER.info("Sparsebundle image on backup server doesnt exist, creating it")
            self.backup_image.create_image()
        elif not self.backup_image.is_mounted():
            LOGGER.info("Mounting sparsebundle image")
            self.backup_image.mount_image()

    def tear_down(self):
        if self.backup_image.is_mounted():
            LOGGER.info("Unmounting sparsebundle image")
            self.backup_image.unmount_image()

        if self.mounter.is_mounted():
            LOGGER.info("Unmounting fileshare on backup server")
            self.mounter.umount()

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
        # removed --delete just in case i screwed up
        self.cmd_line = ['/usr/bin/env', 'rsync', '-av']
        [self.cmd_line.append(x) for x in self._cmdline_builder_from_list("--exclude", self.excludes)]
        [self.cmd_line.append(x) for x in self._cmdline_builder_from_list("--include", self.includes)]

        self.cmd_line.append(self.source_path)
        self.cmd_line.append(self.target_local_destination)

    def execute_backup(self):
        stderr = None
        proc = subprocess.Popen(self.cmd_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, shell=False)
        while proc.returncode is None:
            (stdout, stderr) = proc.communicate()
            for line in stdout.splitlines():
                LOGGER.info("rsync: %s" % line)
        if proc.returncode != 0:
            raise BackupExecutionException("Backup command failed to execute: %s" % stderr)


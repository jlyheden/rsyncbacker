from rsyncbacker.exception import ConfigurationException, BackupExecutionException
from rsyncbacker.hdiutil import ImageManager
from rsyncbacker.mount import MountAfp
from rsyncbacker.util import get_ipv4_addresses_on_host, is_host_on_lan

import logging
import subprocess
from threading import Thread
from Queue import Queue, Empty

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
        self.rsync_verbose = False
        self.source_path = None
        self.cmd_line = []

        self.mounter = None
        self.backup_image = None
        self.post_hook = None

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
            self.excludes = config["rsync"]["excludes"]
        except KeyError:
            LOGGER.info("No excludes set in excludes")

        try:
            self.includes = config["rsync"]["includes"]
        except KeyError:
            LOGGER.info("No includes set in includes")

        try:
            self.rsync_verbose = config["rsync"]["verbose"]
        except KeyError:
            pass

        try:
            self.source_path = config["source"]["path"]
        except KeyError:
            msg = "No source path set in source.path"
            LOGGER.error(msg)
            raise ConfigurationException(msg)

        try:
            self.post_hook = config["post_hook"].split(" ")
        except Exception:
            LOGGER.info("No post_hook configured")

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
        self.cmd_line = ['/usr/bin/env', 'rsync', '-a']
        if self.rsync_verbose:
            self.cmd_line.append("-v")
        self.cmd_line.append("--delete")
        [self.cmd_line.append(x) for x in self._cmdline_builder_from_list("--exclude", self.excludes)]
        [self.cmd_line.append(x) for x in self._cmdline_builder_from_list("--include", self.includes)]

        self.cmd_line.append(self.source_path)
        self.cmd_line.append(self.target_local_destination)

    def execute_backup(self):
        def enqueue_output(out, queue):
            for line in iter(out.readline, b''):
                queue.put(line)
            out.close()

        def get_stderr(out):
            response = []
            for line in iter(out.readline, b''):
                if line == "":
                    break
                response.append(line)
            out.close()
            return "\n".join(response)

        proc = subprocess.Popen(self.cmd_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1,
                                close_fds=True, shell=False)
        q = Queue()
        t = Thread(target=enqueue_output, args=(proc.stdout, q))
        t.daemon = True
        t.start()

        while proc.poll() is None:
            try:
                rsync_line = q.get(timeout=1)
                LOGGER.info("rsync: %s" % rsync_line.strip())
            except Empty:
                pass

        if proc.returncode == 23:
            LOGGER.warning("Some files failed to transfer correctly, output from rsync: %s" % get_stderr(proc.stderr))
        elif proc.returncode == 0:
            LOGGER.info("Rsync completed successfully")
        else:
            LOGGER.error("Rsync failed")
            raise BackupExecutionException("Backup command failed (%s) to execute: %s" % (proc.returncode,
                                                                                          get_stderr(proc.stderr)))

    def post_execute(self):
        if self.post_hook is None:
            return
        p = subprocess.Popen(self.post_hook, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        output = p.communicate()
        if p.returncode != 0:
            raise BackupExecutionException("Post hook failed to execute, output: %s" % output[1])
        return None

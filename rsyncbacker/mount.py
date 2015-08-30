import subprocess
import re
import os
from rsyncbacker.exception import MountAfpException


class Mount(object):

    def __init__(self):
        self.is_mounted_regex = None
        self.exception = BaseException

    def mount_cmd(self, args):
        cmd = ['/usr/bin/env'] + args
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        output = p.communicate()
        if p.returncode != 0:
            raise self.exception("Failed to mount filesystem, output: %s" % output[1])

    def umount_cmd(self, mount_point):
        cmd = ['/usr/bin/env', 'umount', mount_point]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        output = p.communicate()
        if p.returncode != 0:
            raise self.exception("Failed to unmount filesystem, output: %s" % output[1])

    def is_mounted(self):
        p = subprocess.Popen([
            '/usr/bin/env',
            'mount'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        output = p.communicate()
        if p.returncode != 0:
            raise MountAfpException("Failed to list mount points, error: %s" % output[1])
        for line in output[0].splitlines():
            if self.is_mounted_regex.match(line):
                return True
        return False

    def mount(self):
        pass

    def umount(self):
        pass


class MountAfp(Mount):

    def __init__(self, host, share, username, password):
        super(Mount, self).__init__()
        self.host = host
        self.share = share
        self.username = username
        self.password = password
        self.mount_point = os.path.join("/Volumes", self.share)
        self.is_mounted_regex = re.compile('//%s@%s/%s' % (self.username, self.host, self.share))
        self.exception = MountAfpException

    def mount(self):
        source = "afp://%s:%s@%s/%s" % (self.username, self.password, self.host, self.share)
        if not os.path.isdir(self.mount_point):
            os.mkdir(self.mount_point)
        self.mount_cmd(['mount_afp', source, self.mount_point])

    def umount(self):
        self.umount_cmd(self.mount_point)
import subprocess
import os
import re
from rsyncbacker.exception import ImageManagerException


class ImageManager(object):

    def __init__(self, passphrase, loc, mountpoint):
        self.passphrase = passphrase
        self.loc = loc
        self.sparsebundle_loc = "%s.sparsebundle" % loc
        self.mountpoint = mountpoint

    def image_exists(self):
        if os.path.exists(self.sparsebundle_loc):
            return True
        else:
            return False

    def is_mounted(self):
        p = subprocess.Popen([
            '/usr/bin/env',
            'hdiutil',
            'info'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        output = p.communicate()
        if p.returncode != 0:
            raise ImageManagerException("Failed to list hdiutil mounts, error: %s" % output[1])
        for line in output[0].splitlines():
            if re.match('^image-path\s+: %s$' % self.sparsebundle_loc, line):
                return True
        return False

    def create_image(self, size):
        p = subprocess.Popen([
            '/usr/bin/env',
            'hdiutil',
            'create',
            '-stdinpass',
            '-size', size,
            '-fs', 'HFS+',
            '-volname', 'rsyncbackervol',
            '-type', 'SPARSEBUNDLE',
            '-nospotlight',
            '-encryption', 'AES-256',
            self.loc
        ], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        output = p.communicate(input=self.passphrase)
        if p.returncode != 0:
            raise ImageManagerException("Failed to create image in %s, output from hdiutil: %s" % (self.loc, output[1]))

    def mount_image(self):
        p = subprocess.Popen([
            '/usr/bin/env',
            'hdiutil',
            'attach',
            '-stdinpass',
            '-encryption', 'AES-256',
            '-mountpoint', self.mountpoint,
            self.sparsebundle_loc
        ], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        output = p.communicate(input=self.passphrase)
        if p.returncode != 0:
            raise ImageManagerException("Failed to mount image in %s, output from hdiutil: %s" % (self.loc, output[1]))

    def unmount_image(self):
        p = subprocess.Popen([
            '/usr/bin/env',
            'hdiutil',
            'detach',
            self.mountpoint
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        output = p.communicate()
        if p.returncode != 0:
            raise ImageManagerException("Failed to unmount image in %s, output from hdiutil: %s" % (self.loc,
                                                                                                    output[1]))

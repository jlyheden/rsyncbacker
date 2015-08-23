__author__ = 'johan'

from rsyncbacker import RsyncExecutor

import unittest


class TestRsyncExecutor(unittest.TestCase):

    def test_load_config_without_ssh(self):
        config = {
            "target": {
                "host": "backuphost",
                "rsync_name": "backuppath"
            },
            "source": {
                "path": "/"
            }
        }

        backup = RsyncExecutor()
        backup.load_config(config)
        backup.commandline_builder()
        self.assertEqual("/usr/bin/env rsync -a --delete / backuphost::backuppath", " ".join(backup.cmd_line))

    def test_load_config_with_ssh(self):
        config = {
            "target": {
                "host": "backuphost",
                "rsync_path": "/backuppath",
                "use_ssh": True
            },
            "source": {
                "path": "/"
            }
        }

        backup = RsyncExecutor()
        backup.load_config(config)
        backup.commandline_builder()
        self.assertEqual("/usr/bin/env rsync -a --delete -e \"ssh\" / backuphost:/backuppath", " ".join(
            backup.cmd_line))

    def test_load_config_with_ssh_with_excludes_and_includes(self):
        config = {
            "target": {
                "host": "backuphost",
                "rsync_path": "/backuppath",
                "use_ssh": True,
                "ssh_user": "root"
            },
            "source": {
                "path": "/"
            },
            "excludes": [
                "/foo",
                "/bar"
            ],
            "includes": [
                "/bar/baz"
            ]
        }

        backup = RsyncExecutor()
        backup.load_config(config)
        backup.commandline_builder()
        self.assertEqual("/usr/bin/env rsync -a --delete --exclude=/foo --exclude=/bar --include=/bar/baz -e \"ssh -l root\" / backuphost:/backuppath", " ".join(
            backup.cmd_line))

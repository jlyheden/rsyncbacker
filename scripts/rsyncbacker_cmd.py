#!/usr/bin/env python
#
# Copyright 2015 Johan Lyheden
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import logging
import sys

LOGGER = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)

from rsyncbacker import RsyncExecutor, ConfigurationException, BackupExecutionException
from rsyncbacker.util import load_config

parser = argparse.ArgumentParser(description="rsyncbacker backup tool.")
parser.add_argument("-b", "--batch", dest="batch", action="store_true",
                    help="execute in batch mode, without prompts or anything")
parser.add_argument("--ignore-lan-check", dest="ignore_lan_check", action="store_true",
                    help="start backup regardless if target is on same lan as client or not")
parser.add_argument("--no-cleanup", dest="no_cleanup", action="store_true", help="no unmount on failure")
parser.add_argument("config", help="path to configuration yaml")

args = parser.parse_args()

try:
    config = load_config(args.config)
    executor = RsyncExecutor()
    executor.load_config(config)
    executor.commandline_builder()
except ConfigurationException, ex:
    LOGGER.error(ex)
    sys.exit(1)

if not args.ignore_lan_check and executor.should_backup_run() is False:
    LOGGER.info("Refusing to start backup since target is on another network")
    sys.exit(0)

# TODO: prompt and execute
try:
    executor.set_up()
except Exception, ex:
    LOGGER.error("Failed to set up, exception %s" % ex.message)
    sys.exit(1)

try:
    LOGGER.debug("Will execute %s" % " ".join(executor.cmd_line))
    executor.execute_backup()
except Exception, ex:
    LOGGER.exception("Backup execution failed")
else:
    try:
        executor.post_execute()
    except BackupExecutionException, ex:
        LOGGER.warning("Failed to execute post hook %s" % ex)
finally:
    if not args.no_cleanup:
        try:
            executor.tear_down()
        except Exception, ex:
            LOGGER.error("Failed to tear down, exception %s" % ex.message)
            sys.exit(1)

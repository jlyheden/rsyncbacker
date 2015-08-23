#!/usr/bin/env python

import argparse
import logging
import sys

LOGGER = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)

from rsyncbacker import RsyncExecutor, ConfigurationException
from rsyncbacker.util import load_config

parser = argparse.ArgumentParser(description="rsyncbacker backup tool.")
parser.add_argument("-b", "--batch", dest="batch", action="store_true",
                    help="execute in batch mode, without prompts or anything")
parser.add_argument("--ignore-lan-check", dest="ignore_lan_check", action="store_true",
                    help="start backup regardless if target is on same lan as client or not")
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
LOGGER.debug(executor.cmd_line)
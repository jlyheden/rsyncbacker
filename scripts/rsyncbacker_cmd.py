#!/usr/bin/env python

import argparse
import logging
import sys

LOGGER = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)

from rsyncbacker import RsyncExecutor, ConfigurationException
from rsyncbacker.util import load_config

parser = argparse.ArgumentParser(description="rsyncbacker backup tool.")
parser.add_argument("-b", "--batch", dest="batch", action="store_true", help="execute in batch mode, without prompts or anything")
parser.add_argument("--skip-routed", dest="skip_routed", action="store_true", help="don't start backup if on remote network")
parser.add_argument("config", help="path to configuration yaml")

args = parser.parse_args()

try:
    config = load_config(args.config)
    executor = RsyncExecutor()
    executor.load_config(config)
    executor.commandline_builder()
except ConfigurationException, ex:
    LOGGER.error(ex)

if not args.skip_routed and executor.should_backup_run() is False:
    LOGGER.info("Refusing to start backup since target is on another network")
    sys.exit(0)

# TODO: prompt and execute
LOGGER.debug(executor.cmd_line)
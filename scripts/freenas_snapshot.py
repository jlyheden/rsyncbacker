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
import requests
import json
import datetime
import yaml
import logging

LOGGER = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)


class FreeNAS(object):

    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.suffix = "_rsyncbacker"

    def _get(self, path):
        req = requests.get("http://%s%s" % (self.host, path), auth=(self.username, self.password))
        LOGGER.debug("Response: %s" % req.text)
        return json.loads(req.text)

    def _delete(self, path):
        req = requests.delete("http://%s%s" % (self.host, path), auth=(self.username, self.password))
        LOGGER.debug("Response: %s" % req.text)
        return req.status_code == 204

    def _post(self, path, data, headers):
        req = requests.post("http://%s%s" % (self.host, path), auth=(self.username, self.password),
                            data=json.dumps(data), headers=headers)
        LOGGER.debug("Response: %s" % req.text)
        return req.status_code == 201

    def get_all_fs_snapshots(self, filesystem):
        offset = 0
        limit = 1000
        snapshots = []
        while True:
            response = self._get("/api/v1.0/storage/snapshot/?offset=%s&limit=%s" % (offset, limit))
            snapshots.extend([x for x in response if x["filesystem"] == filesystem
                              and x["fullname"].endswith(self.suffix)])
            if len(response) < limit:
                break
            else:
                offset += 1
        return snapshots

    def delete_snapshots(self, snapshots, number_to_keep):
        if len(snapshots) < number_to_keep:
            LOGGER.info("Only found %s snapshots so skipping house keeping" % len(snapshots))
            return
        for snapshot in sorted(snapshots, key=lambda k: k["name"], reverse=True)[number_to_keep:]:
            self._delete("/api/v1.0/storage/snapshot/%s/" % snapshot["fullname"])

    def create_snapshot(self, filesystem):
        data = {
            "dataset": filesystem,
            "name": "%s%s" % (datetime.datetime.now().strftime("%Y%m%d_%H%M%S"), self.suffix)
        }
        headers = {
            "Content-Type": "application/json"
        }
        self._post("/api/v1.0/storage/snapshot/", data, headers)


parser = argparse.ArgumentParser(description="simple freenas snapshot manager")
parser.add_argument("config", help="path to configuration yaml")
parser.add_argument("filesystem", help="filesystem to snapshot")
parser.add_argument("-n", "--number-to-keep", dest="number_to_keep", default=30, help="number of snapshots to keep")

args = parser.parse_args()

config = yaml.load(open(args.config).read())

freenas_api = FreeNAS(config["host"], config["username"], config["password"])
freenas_api.create_snapshot(args.filesystem)
all_snapshots = freenas_api.get_all_fs_snapshots(args.filesystem)
freenas_api.delete_snapshots(all_snapshots, int(args.number_to_keep))

LOGGER.info("Done")
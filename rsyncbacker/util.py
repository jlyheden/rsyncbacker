from rsyncbacker.exception import ConfigurationException

import subprocess
import re
import logging
import yaml
import socket

LOGGER = logging.getLogger(__name__)


def load_config(yml_file):
    try:
        return yaml.load(open(yml_file).read())
    except IOError, ex:
        msg = "Failed to load config file %s" % yml_file
        LOGGER.error(msg)
        raise ConfigurationException(msg, ex)


def hex_to_dotted(value):
    hex_value = value.split("x")
    return ".".join([str(int("%sx%s" % (hex_value[0], hex_value[1][x:x+2]), 0)) for x in xrange(0,
                                                                                                len(hex_value[1]), 2)])


def ip_to_hex(ip):
    split = ip.split(".")
    return "0x{:02X}{:02X}{:02X}{:02X}".format(*map(int, split))


def get_ipv4_addresses_on_host():
    rv = []
    p = subprocess.Popen(['/usr/bin/env', 'ifconfig', '-a'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         shell=False)
    output = p.communicate()
    if p.returncode != 0:
        raise ConfigurationException("Failed to identify my local IP-addresses, output: %s" % output[1])

    pattern = re.compile("^\s+inet ([0-9\.]+) netmask ([0-9]x[0-9a-f]{8}) broadcast ([0-9\.]+)$")
    for line in output[0].splitlines():
        result = re.match(pattern, line)
        if result:
            rv.append({
                "ip": result.group(1),
                "netmask": hex_to_dotted(result.group(2)),
                "broadcast": result.group(3)
            })
    return rv


def get_ipv4_network(ip, netmask):
    ips = [int(x) for x in ip.split(".")]
    nms = [int(x) for x in netmask.split(".")]
    return "%s.%s.%s.%s" % ((ips[0] & nms[0]), (ips[1] & nms[1]), (ips[2] & nms[2]), (ips[3] & nms[3]))


def get_ip_from_unknown(value):
    if re.match("[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", value):
        return value
    else:
        return socket.gethostbyname(value)


def is_host_on_lan(host, ifaces):
    host = get_ip_from_unknown(host)
    for network in [get_ipv4_network(x["ip"], x["netmask"]) for x in ifaces]:
        if network in [get_ipv4_network(host, x["netmask"]) for x in ifaces]:
            return True
    return False

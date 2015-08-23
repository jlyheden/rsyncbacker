__author__ = 'johan'

import unittest
from rsyncbacker.util import *


class TestUtils(unittest.TestCase):

    def test_ip_to_hex(self):
        self.assertEquals("0x73FF0861", ip_to_hex("115.255.8.97"))

    def test_hex_to_dotted(self):
        self.assertEquals("255.255.255.0", hex_to_dotted("0xffffff00"))

    def test_get_ipv4_network(self):
        self.assertEquals("192.168.0.0", get_ipv4_network("192.168.0.1", "255.255.255.0"))

    def test_get_ip_from_unknown(self):
        self.assertEquals("127.0.0.1", get_ip_from_unknown("127.0.0.1"))
        self.assertEquals("127.0.0.1", get_ip_from_unknown("localhost"))

    def test_is_host_on_lan_one_interface(self):
        ifaces = [
            {
                "ip": "192.168.1.10",
                "netmask": "255.255.255.0"
            }
        ]
        self.assertTrue(is_host_on_lan("192.168.1.150", ifaces))
        self.assertFalse(is_host_on_lan("192.168.2.150", ifaces))

    def test_is_host_on_lan_two_interfaces(self):
        ifaces = [
            {
                "ip": "192.168.1.10",
                "netmask": "255.255.255.0"
            },
            {
                "ip": "10.0.0.123",
                "netmask": "255.0.0.0"
            }
        ]
        self.assertTrue(is_host_on_lan("192.168.1.150", ifaces))
        self.assertFalse(is_host_on_lan("192.168.2.150", ifaces))
        self.assertTrue(is_host_on_lan("10.100.23.54", ifaces))
        self.assertFalse(is_host_on_lan("172.16.0.4", ifaces))

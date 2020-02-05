import unittest
import argparse
import sys
import urllib.parse
import re
import tmadog_server
import requests
import threading

class ServerTest (unittest.TestCase):

    url = None
    local = True
    server = None
    thread = None

    @classmethod
    def setUpClass (cl):
        if cl.local:
            cl.thread = threading.Thread (target = cl.server.serve_forever)

            cl.thread.start ()

            return


    @classmethod
    def tearDownClass (cl):
        if cl.local:
            cl.server.shutdown ()

        return

    def test_homepage (self):

        res = requests.get (self.url)

        self.assertEqual (res.status_code, 200, '''Ping the server's index page''')


argv = sys.argv

parser = argparse.ArgumentParser ()

grp_parser = parser.add_mutually_exclusive_group (required = True)

grp_parser.add_argument ('--local', action = 'store_true', help = 'Whether the server is on this machine')

grp_parser.add_argument ('--url', help = 'Whether the server is on this machine')

args, ukn = parser.parse_known_args (argv or [])

if args.local:
    ServerTest.server, ukn = tmadog_server.main (argv = ukn)

    ServerTest.url = urllib.parse.urlparse ('http://%s:%d/' % ServerTest.server.server_address).geturl ()

else:
    ServerTest.url = args.url  



if __name__ == '__main__':
    unittest.main (argv = ukn)

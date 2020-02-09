import unittest
import argparse
import sys
import urllib.parse
import re
import tmadog_server
import requests
import threading
from navigation import Navigation 
import configparser
import http.server
from qstmgt import QstMgt  

class ServerTest (unittest.TestCase):

    url = None
    local = True
    server = None 

    map = configparser.ConfigParser (interpolation =
        configparser.ExtendedInterpolation ())


    @classmethod
    def setUpClass (cl):
        if cl.local:
            cl.thread = threading.Thread (target = cl.server.serve_forever)

            cl.thread.start ()

        cl.std_cred = ['Nou133606854', '12345']

        cl.qmap = cl.map ['qmap']

        try:
            cl.std_nav = Navigation.Navigator (
                    cl.url,
                    cl.map, 
                    {
                        '[Matric Number]': cl.std_cred [0],
                        '[Password]': cl.std_cred [1] 
                        }
                    )
            
            t = cl.std_nav ('tma_page')[:-1]
            cl.std_qmgr = QstMgt.QstMgr (
                    matno = cl.std_cred [0],
                    crscode = 'CIT701',
                    tma = 1,
                    fargs = t[0],
                    url = t[1].url,
                    qmap = cl.qmap,

                    )

        except BaseException as err:
            cl.tearDownClass ()
            raise err

        return


    @classmethod
    def tearDownClass (cl):
        if cl.local:
            cl.server.shutdown ()

        return

    def test_homepage (self):

        res = self.std_nav['home']

        self.assertEqual (res.status_code, 200, '''Ping the server's index page''')

    def test_login (self):
        
        std_nav = Navigation.Navigator (
                self.url,
                self.map, 
                {
                    '[Matric Number]': 'Nou123456789',
                    '[Password]': 'sheriff'
                    }
                )

        for r in std_nav ['profile_page'], self.std_nav ['profile_page']:

            p = re.search (r'nou\d{9}', r.request.body or r.request.url, re.I).group (0)

            with self.subTest (
                    'Login Tests',
                    r = r,
                    p = p
                    ):
                self.assertIsNotNone (re.search (p, r.text, flags = re.I), 'Navigator can log a user in')

        return

    def test_qstmgr (self):
        qst = self.std_qmgr.fetch ()

        assertTrue (hasattr (qst, 'keys'))
        


    def test_ans (self):
        pass

def main (argv = []):

    parser = argparse.ArgumentParser ()

    parser.add_argument ('--config', default = 'myrc', help = 'configuration file to use')

    grp_parser = parser.add_mutually_exclusive_group (required = True)

    grp_parser.add_argument ('--local', action = 'store_true', help = 'Whether the server is on this machine')

    grp_parser.add_argument ('--url', help = 'The remote url if no local server')

    args, ukn = parser.parse_known_args (argv or [])

    if args.local:
        ServerTest.server, ukn = tmadog_server.main (argv = ukn)

        ServerTest.url = urllib.parse.urlparse ('http://%s:%d/' % ServerTest.server.server_address).geturl ()

    else:
        ServerTest.url = args.url  

    ServerTest.map.read (args.config)
    
    return unittest.main (argv = ukn)



if __name__ == '__main__':
    main (sys.argv)

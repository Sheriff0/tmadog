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
from ansmgt import AnsMgt

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

        cl.sess = requests.Session ()

        try:
            cl.std_nav = Navigation.Navigator (
                    cl.url,
                    cl.map, 
                    {
                        '[Matric Number]': cl.std_cred [0],
                        '[Password]': cl.std_cred [1] 
                        },
                    session = cl.sess
                    )
            
            t = cl.std_nav ('tma_page')[:-1]
            cl.std_qmgr = QstMgt.QstMgr (
                    matno = cl.std_cred [0],
                    crscode = 'CIT701',
                    tma = 1,
                    fargs = t[0],
                    url = t[1].url,
                    qmap = cl.qmap,
                    session = cl.sess

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

    def test_QA_mgrs (self):
       
        fargs = self.std_qmgr.fargs.copy ()
        fargs [self.std_qmgr.dt0] = self.std_qmgr.fargs [self.std_qmgr.dt0].copy ()

        qstmgr = QstMgt.QstMgr (
                matno = self.std_cred [0],
                crscode = 'CSS133',
                tma = 2,
                fargs = fargs,
                stop = 7,
                url = self.std_qmgr.referer,
                qmap = self.qmap,
                session = self.std_qmgr.session

                )

        qst = self.std_qmgr.fetch ()


        self.assertTrue (hasattr (qst, 'keys'), 'Question should be dictionary-like')
        
        x = (self.qmap [k] for k in self.qmap if k not in ('indices', 'volatile', 'pseudo_ans'))

        for k in x:
            with self.subTest ('Qmap should be valid', k = k):
                self.assertIn (k, qst, '%s should be in qst' % (k,))
        
        norm_ansmgr = AnsMgt.AnsMgr (
                qmap = self.qmap,
                pseudo_ans = self.qmap ['pseudo_ans'].split (','),
                database = 'pg/olddb',
                mode = AnsMgt.ANS_MODE_NORM,
                )

        hack_ansmgr = AnsMgt.AnsMgr (
                qmap = self.qmap,
                pseudo_ans = self.qmap ['pseudo_ans'].split (','),
                database = 'pg/olddb',
                mode = AnsMgt.ANS_MODE_HACK,
                )

        qst1 = qstmgr.fetch ()
        
        self.assertTrue (hasattr (qst1, 'keys'), 'Question should be dictionary-like')

        while True:

            t = self.std_qmgr.fetch ()
            if t:
                q = norm_ansmgr.answer (t)
                p = self.std_qmgr.submit (q)
                norm_ansmgr.check (q, p)

            t1 = qstmgr.fetch ()
            if t1:
                q1 = hack_ansmgr.answer (t1)
                p1 = qstmgr.submit (q1)

                hack_ansmgr.check (q1, p1)

            if t is False and t1 is False:
                break

            for k, r, amgr in zip (
                    [q, q1],
                    [p, p1],
                    [norm_ansmgr, hack_ansmgr]
                    ):
                with self.subTest ('Feedback Time', r = r, k = k, amgr = amgr):
                    self.assertTrue (
                            (r is 1 and k ['ans'] == amgr (k, 'ans')) or (r is 0 and k ['ans'] != amgr (k, 'ans')),
                            'QstMgr can give feedback on submits')


        self.assertTrue (
                self.std_qmgr.count == 10 and qstmgr.count == 7,
                'Qstmgr can stop fetching questions after fetching "stop" (server side numbering) number of questions'
                )


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

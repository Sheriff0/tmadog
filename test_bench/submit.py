import sqlite3
import re
import requests
import dogs
import builtins
import random
import lxml
from pathlib import PurePath
import collections
import cfscrape
import os
import sys
import argparse
import configparser
from urllib import parse
from navigation import Navigation
from qstmgt import QstMgt
from ansmgt import AnsMgt
import io
import parse


class Submit (object):
    '''This command submit your TMAs faster and more efficiently.
    '''

    setup = {
	    'name' : 'submit',

	    'formatter_class' : argparse.RawDescriptionHelpFormatter,

	    'fromfile_prefix_chars' : '@',

	    }

    options = [

            [
                (
                    '--matno',
                    ),
                {

                    'action': 'append',

                    'help': '''The target Matriculation Number. E.g Nou123456789
                ''',

                'type': str,

                'required': True,

                }
                ],

            [
                (
                    '--pwd',
                    ),

                {
                    'action': 'append',

                    'help': '''The accompanying password. E.g 12345.
                ''',

                'type': str,

                'required': True,

                }
                ],

            [
                (
                    '--tmano',
                    ),

                {
                    'action': 'append',

                    'help': '''The tma to submit.
                ''',

                'required': True,

                }
                ],


            [
                (
                    '--crscode',
                    ),

                {
                    'action': 'append',

                    'help': '''The course to submit.
                ''',

                'required': True,

                }
                ],

            [
                (
                    '--verbose',
                    ),

                {
                    'action': 'store_true',

                    'help': '''Whether you want a summary of the operation's results''',

                }
                ],

            [
                (
                    '--jobs',
                    ),

                {

                    'help': '''To use jobs.
                ''',

                'type': int,

                'default': 0,
                }
                ],

            [
                (
                    '--mode',
                    ),

                {

                    'help': '''The submission mode.
                ''',

                'default': AnsMgt.AnsMgr.ANS_MODE_NORM,

                'choices': [
                    AnsMgt.AnsMgr.ANS_MODE_MAD,
                    AnsMgt.AnsMgr.ANS_MODE_HACK,
                    AnsMgt.AnsMgr.ANS_MODE_NORM,
                    ],
                'type': int
                }
                ],

            [
                (
                    '--stop',
                    ),

                {

                    'help': '''The number of questions to submit.
                ''',

                'default': 10,

                'type': int,
                }
                ],
            ]

    @classmethod
    def main (
            cl,
            args: argparse.Namespace,
            ) -> None :

        if args.jobs:
            cl.run_jobs (args)
        else:
            cl.submit (args)


    @classmethod
    def submit (cl, args):
        std = {}
        ansmgr = AnsMgt.AnsMgr (
                qmap = args.map ['qmap'],
                database = args.database,
                mode = args.mode,
                pseudo_ans = args.map ['qmap']['pseudo_ans'].split (','),
                interactive = False,
                )

        nav = Navigation.Navigator (
                args.url,
                args.map,
                {
                    },
                timeout = (30.5, 60),
                session = cfscrape.create_scraper (),
                )

        for i, m in enumerate (args.matno):

            std [args.map ['kmap']['matno']] = m

            try:
                std [args.map ['kmap']['pwd']] = args.pwd [i]
                std ['crscode'] = args.crscode [i]
                std ['tmano'] = args.tmano [i]
            except:
                pass

            finally:
                nav.keys = std
                nav ['profile_page']

                if 'tma_page:-1' not in nav:
                    nav ('tma_page')[-1]

                qstmgr = QstMgt.QstMgr (
                        fargs = nav ['tma_page:-1'][0],
                        url = nav ['tma_page:-1'][1].url,
                        matno = nav.keys [args.map ['kmap']['matno']],

                        tma = nav.keys ['tmano'],

                        crscode = nav.keys ['crscode'],
                        qmap = nav.webmap ['qmap'],
                        stop = args.stop,
                        session = nav.session
                        )

                res = cl._submit (nav, ansmgr, qstmgr)
                print (res)

                nav.traverse_deps = False

                nav ['logout_page']

                nav.traverse_deps = True



    @classmethod
    def _submit (cl, navigator, ansmgr, qstmgr):

        qst = qstmgr.fetch ()

        while qst:
            qst = ansmgr.answer (qst)

            if qst == ansmgr.NOANSWER:
                if not qstmgr.stop:
                    qstmgr.stop = True
                    while qst == ansmgr.NOANSWER:
                        qst = qstmgr.fetch ()
                        qst = ansmgr.answer (qst)

                    qstmgr.stop = False
                    r = qstmgr.submit (qst)
                    ansmgr.check (qst, r)

            elif qst == ansmgr.NOCOURSE:
                return qst
            else:
                r = qstmgr.submit (qst)
                ansmgr.check (qst, r)


            qst = qstmgr.fetch ()

        res = re.search (r'(?P<score>\d+)\W+?out\W+?of\W+?(?P<total>\d+)',
                qstmgr.sres.text, flags = re.I | re.M)
        if not res:
            qstmgr.stop = False
            qstmgr.fetch
            res = re.search (r'(?P<score>\d+)\W+?out\W+?of\W+?(?P<total>\d+)',
                    qstmgr.qres.text, flags = re.I | re.M)

        return res.group (0) if res else res


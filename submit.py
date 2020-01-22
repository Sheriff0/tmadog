import sqlite3
import re
import requests
import dogs
import builtins
import random
import lxml
from pathlib import PurePath
import collections
from tmadog_utils import TmadogUtils
import cfscrape
import os
import sys
import argparse
import configparser
from urllib import parse

class Submit (object):
    cmd_des = {
	    'name' : 'submit',

	    'description' : '''This command simply submits TMA(s) for you. Give it a Matric No / password pair and go to bed - let it do the hard work for you.
	    ''',
	    'formatter_class' : argparse.RawDescriptionHelpFormatter,

	    'fromfile_prefix_chars' : '@',

	    }

    opt_des = [
            {
                'id': [
                    '--matno',
                    ],

                'action': 'append',
                
                'help': '''The target Matriculation Number. E.g Nou123456789
                ''',

                'type': str,

                #'nargs': '+',

                'required': True,

                },

            {
                'id': [
                    '--pwd',
                    ],

                'action': 'append',
                
                'help': '''The accompanying password. E.g 12345.
                ''',

                'type': str,

                #'nargs': '+',

                'required': True,

                },
            {
                'id': [
                    '--tma',
                    ],

                'action': 'append',
                
                'help': '''The tma to submit.
                ''',


                #'nargs': '+',

                'required': True,

                },
            ]


    def submit (
            args: argparse.Namespace,
            config: configparser.SectionProxy
            ) -> None :
        ''' Submit your TMAs faster and efficiently.

        The function takes any object with the following attributes:
            - matno: The target Matriculation number of the TMA. e.g NOUxxxxxxxxx.

            - pwd: The accompanying password.

            - tma: The target TMA number. If this is not given, the function will try
              to submit all the TMAs..

            - session: The session to use for the submission. The is required for
              cookie-persistence. The session object must be an instance of
              requests.Session or its subclass.
        '''
        
        tmadogsess = cfscrape.create_scraper ()

        defhdr = {
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                #'sec-fetch-site': 'same-origin'
                }

        tmadogsess.headers.update (defhdr)
        if args.cookie:
            cookie = configparser.ConfigParser ()
            cookie.read (args.cookie)

            requests.utils.add_dict_to_cookiejar (tmadogsess, cookie.get
                    ('cookies', {}))
        

        xpage = tmadogsess.get (
                url.geturl (),
                headers = {
                    'referer': args.url,
                    'host': parse.urlparse (args.url).hostname
                    }
                )

        xpage.raise_for_status()
        
        buttons = config['login_form']['home_page'].strip ().split (',')
        
        tb = config['question-form']['tma_page'].strip ().split (',')[0]

        qn = config[configparser.DEFAULTSECT]['qn_name'].strip ()

        pgcache = {}

        xpage = nav_to (
                session = tmadogsess,
                html = xpage.text,
                url = xpage.url,
                buttons = buttons
                )

        pgcache['login_form'] = xpage

        for midx, matno in enumerate (args.matno):
            ppage = TmadogUtils.login (
                    pgcache['login_form'].text,
                    pgcache['login_form'].request.url,
                    session = tmadogsess,
                    matno = matno,
                    pwd = args.pwd[midx]
                    )

            if 'tma-page' is not in pgcache:
                buttons = config['tma_page']['profile_page'].strip ().split (',')
                xpage = nav_to (
                        session = tmadogsess,
                        buttons = buttons,
                        html = ppage.text,
                        url = ppage.url
                        )
                pgcache['tma_page'] = xpage

            tmas = args.tma[midx].strip ().split (',')

            for tma in range (int (tmas[0]), int (tmas[-1]) + 1):
                qfetcher = TmadogUtils.QstMgr (
                        
                        session = tmadogsess,
                        url = pgcache['tma_page'].url,
                        matno = matno,
                        tma = tma,
                        crscode = args.crscode[midx],
                        html = pgcache['tma_page'].text,
                        button = tb,
                        )

                db_data = TmadogUtils.submitter(
                        session = tmadogsess,
                        tma_handle = qfetcher,
                        qhandler,
                        stp = 10,
                        qnref = 'qj',
                        ans = 'ans',
                        #NOTE: **qhandler_args,
                        )

                print ('success: TMA%i for %s has been submitted' % (tma, matno))

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


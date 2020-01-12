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

class Submit (object):
    cmd_des = {
	    'name' : 'submit',

	    'description' : '''This command simply submits TMA(s) for you. Give it a Matric No / password and go to bed - let it do the hard work for you.

	    ''',
	    'formatter_class' : argparse.RawDescriptionHelpFormatter,

	    'fromfile_prefix_chars' : '@',
	    }

    opt_des = [
            {
                'id': [
                    '--matno',
                    ],

                'dest': 'matno',

                'action': 'append',
                
                'help': '''The target Matriculation Number. E.g Nou123456789
                ''',

                'type': str,

                'nargs': '+'

                },

            {
                'id': [
                    'matno'
                    ],


                'action': 'append',
                
                'help': '''The target Matriculation Number. E.g Nou123456789
                ''',

                'type': str,

                },

            {
                'id': [
                    '--pwd',
                    ],

                'dest': 'pwd',

                'action': 'append',
                
                'help': '''The accompanying password. E.g 12345.
                ''',

                'type': str,

                'nargs': '+'

                },
            {
                'id': [
                    'pwd',
                    ],

                'action': 'append',
                
                'help': '''The accompanying password. E.g 12345.
                ''',

                'type': str,

                },
            ]

    def submit (
            args: argparse.Namespace
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

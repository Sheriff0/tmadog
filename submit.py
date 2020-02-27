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

                #'nargs': '+',

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

                #'nargs': '+',

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


                #'nargs': '+',

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


                #'nargs': '+',

                'required': True,

                }
                ],
            ]

    @staticmethod
    def main (
            args: argparse.Namespace,
            ) -> None :
        print (args)

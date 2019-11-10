import sys
import cfscrape
import os
from dogs import *
#import tmadog_utils
import argparse

tmadogsess = cfscrape.create_scraper ()

defhdr = {
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-site': 'same-origin'
        }

tmadogsess.headers.update (defhdr)

def main ():
    tmadogparser = argparse.ArgumentParser(
            prog = 'tmadog', 
            
            description = '''
                tmadog will not only submit you TMAs faster, it can
                also hack the TMA database''',
            
            usage = '''
            tmadog [option [...]] [file [...]]''',
            fromfile_prefix_chars = '@',
            epilog = 'Author: smeO\n'
            )

    tmadogcmds = tmadogparser.add_mutually_exclusive_group (required = True)

    tmadogcmds.add_argument (
            '--submit',
            action = 'store_true',
            help = '''
            Submit TMA the normal way
            '''
            )

    tmadogcmds.add_argument (
            '--hack',
            action = 'store_true',
            help = '''
            Submit TMA with some hacks
            '''
            )
    try:
        tmadogparser.parse_args()

    except argparse.ArgumentError:
        print ('Errs')

if __name__ == '__main__':
        main ()

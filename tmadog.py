import sys
import cfscrape
import os
from dogs import *
#import tmadog_utils
import argparse
from submit import Submit

tmadogsess = cfscrape.create_scraper ()

defhdr = {
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-site': 'same-origin'
        }

tmadogsess.headers.update (defhdr)

main_psr = argparse.ArgumentParser (
        #usage = '''tmadog [-h | --help] COMMAND [cmd_args [...]]
        #''',
        )

main_psr.add_argument (
        '--database', '-db', 
        default = 'tmadogdb',
        type = str,
        dest = 'database',
        help = '''Select the database to use.'''
        )


main_psr.add_argument (
        '--url', '-U', 
        default = 'https://www.nouonline.net/',
        type = str,
        dest = 'url',
        help = '''The NOUN website to use.'''
        )


cmds = main_psr.add_subparsers (

        required = True,
        title = 'COMMAND',
       # metavar = '''
       # submit
       # hack
       # ''',
        )

cmd_submit_psr = cmds.add_parser ( **Submit.cmd_des)

for p, m in [
        (cmd_submit_psr, Submit),
        ]:
    for opt in m.opt_des:
        p.add_argument (*opt['id'].copy (), **{k: opt[k] for k in opt if k is not 'id'})



#def main ():
#    pass
#
#if __name__ == '__main__':
#        main ()

import sys
import cfscrape
import os
from dogs import *
#import tmadog_utils
import argparse
from submit import Submit
import configparser


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

main_psr.add_argument (
        '--cookie',
        type = str,
        help = '''Reuse a session saved in a file''',
        default = None,
        )

main_psr.add_argument (
        '--config-file',
        '-cf',
        type = str,
        help = '''The config file to use aside the default '.tmadogrc' file''',
        default = '.tmadogrc',
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

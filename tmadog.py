import sys
import cfscrape
import os
from dogs import *
#import tmadog_utils
import argparse
from submit import Submit
import configparser


class Commands:
    def __init__ (self, **kwargs):
        for k in kwargs:
            setattr (self, k, kwargs [k])

        return

    def __iter__ (self):
        for k in self.__dict__.copy ():
            if k.endswith ('cmd'):
                yield k

    def __next__ (self):
        return self.__iter__ ()

    def __call__ (self, cmd, args):
        c = (k for k in self.__dict__ if k.startswith (cmd))
        try:
            return getattr (self, next (c)).main (args)
        except StopIteration:
            raise KeyError ('No command %s found' % (cmd,))

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
        '--map',
        '--config',
        dest = 'map',
        type = str,
        help = '''The config file to use aside the default 'dogrc' file''',
        default = 'dogrc',
        )


commands = Commands (submit_cmd = Submit)

cmds_parser = main_psr.add_subparsers (

        title = 'COMMAND',
        dest = 'command',
       # metavar = '''
       # submit
       # hack
       # ''',
        )

for c in commands:
    c1 = c + '_psr'
    c = getattr (commands, c)
    setattr (commands, c1, cmds_parser.add_parser ( **c.setup, description = c.__doc__))
    for opt in c.options:
        getattr (commands, c1).add_argument (*opt [0], **opt [1])

args = main_psr.parse_args ()

mp = configparser.ConfigParser (interpolation =
        configparser.ExtendedInterpolation ())

mp.read (args.map)
args.map = mp

if args.command:
    commands (args.command, args)

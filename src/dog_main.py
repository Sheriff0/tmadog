import time
import math
import unittest
import argparse
import sys
import urllib.parse
import re
import requests
import navigation
import configparser
import ansm
import dbm
import lxml
import scrm
import copy
import json
import cloudscraper
import cookie_parse
import dogs
import qstwriter
import pathlib


import libdogs
import simple_dog


def getcookie(nav, args = None):
    if not args:
        fi = input("""
Please input a cookie file (e.g from the browser)--> """);

    else:
        fi = args.cookies;

    session = libdogs.session_from_cookies(nav.keys[libdogs.P_URL], fi);
    if session:
        nav.session = session;
    return nav;

def main (args):

    def cleanup():
        if ansmgr._cur:
            ansmgr.close ()

        f = open (args.qstdump, 'w') if args.debug else None

        if args.updatedb:
            dbm.update_hacktab (args.database, ansmgr.iter_cache (),
                    ansmgr.qmap, fp = f)
        if args.debug or args.output:
            arr = []
            for qst in ansmgr.iter_cache ():
               arr.append (qst)
            
            if args.debug:
                json.dump (arr, f)

            if args.output:
                qstwriter.fromlist(arr, ansmgr.qmap, qstwriter.writeqst(args.output));

        if f:
            f.close ()



    mp = configparser.ConfigParser (interpolation =
        configparser.ExtendedInterpolation ())

    mp.read (args.wmap)

    args.wmap = mp;

    ansmgr = ansm.AnsMgr (
            qmap = mp['qmap'],
            database = args.database,
            mode = ansm.ANS_MODE_NORM,
            pseudo_ans = mp['qmap']['pseudo_ans'].split (','),
            )
    
    dog = simple_dog.SimpleDog(libdogs.preprocess(args), ansmgr);

    try:
        task = dog._InternalTask(args = args);
        dog.submit(task);

    except KeyboardInterrupt:
        cleanup();

    except BaseException as err:
        cleanup();
        raise err;
    

    return cleanup();


if __name__ == '__main__':

    parser = argparse.ArgumentParser ();

    parser.add_argument ('--matno', help = 'Your Matric Number', nargs = "+", action = libdogs.AppendList, dest = libdogs.P_USR);

    parser.add_argument ('--pwd', help = 'Your password', nargs = "+", action = libdogs.AppendList, dest = libdogs.P_PWD);

    parser.add_argument ('--crscode', help = 'Your target course', nargs = "+", action = libdogs.AppendList, dest = libdogs.P_CRSCODE);

    parser.add_argument ('--tma', nargs = "+", help = 'Your target TMA for the chosen course', action = libdogs.AppendList, dest = libdogs.P_TMA);

    parser.add_argument ('--config', default = 'dogrc', help = 'configuration file to use', dest = libdogs.P_WMAP);

    parser.add_argument ('--debug', action = 'store_true', help = 'To enable debug mode')

    parser.add_argument ('--qstdump', default = 'dumpqst.json', help = 'The dump file for questions')

    parser.add_argument ('--database', '-db', default = 'olddb', help = 'The database to use')

    parser.add_argument ('--noupdatedb', '-nodb', action = 'store_false', dest = 'updatedb', default = True, help = 'Update the database in use')

    parser.add_argument ('--url', help = 'The remote url if no local server', action = libdogs.AppendList, required = True, dest = libdogs.P_URL)


    parser.add_argument ('--cookies', help = 'Website cookies');

    parser.add_argument ('--output', help = "output file format");

    args = parser.parse_args()

    main (args);

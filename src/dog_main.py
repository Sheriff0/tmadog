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
import os

import logging
import libdogs
import simple_dog




def main (args, pkg_name):

    pkg_name = pathlib.Path(pkg_name);

    pkg_dir = pathlib.Path(os.sep.join(str(pkg_name.resolve()).split(os.sep)[:-1]));

    logger = logging.getLogger('tmadog');

    logger.setLevel(logging.DEBUG);
    # create file handler which logs even debug messages
    dfh = logging.FileHandler(str(pkg_dir.joinpath('debug.log')), mode = "w");
    dfh.setLevel(logging.DEBUG);

    fatal = logging.FileHandler(str(pkg_dir.joinpath('fatal.log')), mode = "w");
    fatal.setLevel(logging.CRITICAL);

    stdout = logging.StreamHandler();
    stdout.setLevel(logging.INFO);

    dfh.setFormatter(logging.Formatter('%(asctime)s: %(name)s: %(levelname)s: %(message)s'));

    stdout.setFormatter(logging.Formatter('%(name)s: %(levelname)s: %(message)s'));

    # add the handlers to the logger
    logger.addHandler(dfh);
    logger.addHandler(fatal);
    logger.addHandler(stdout);


    def getcookie(nav):

        if not args.cookies:
            fi = pathlib.Path(input("""
    
Please input a cookie file (e.g from the browser)--> """));


        else:
            fi = pathlib.Path(args.cookies);
            args.cookies = None;

        session = libdogs.session_from_cookies(nav.keys[libdogs.P_URL], str(fi));
        if session:
            nav.session = session;
        return nav;
    

    def get_nav(cli):
        nonlocal dog;
        if dog.nav:
            nav = dog.nav;
            dog.nav = libdogs.lazy_nav_reconf(nav, cli);
        else:
            nav = navigation.Navigator(cli[libdogs.P_URL], cli[libdogs.P_WMAP], cli);
            nav = getcookie(nav);
            dog.nav = nav;

        return dog.nav;

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
    
    if not getattr(args, libdogs.P_WMAP):
        logger.info("no config file given, setting default config file for webmap");
        setattr(args, libdogs.P_WMAP, str(pkg_dir.join("nourc")));

    mp = configparser.ConfigParser (interpolation =
        configparser.ExtendedInterpolation ())
    
    logger.info("reading config file and initializing a webmap");
    mp.read (getattr(args, libdogs.P_WMAP));

    setattr(args, libdogs.P_WMAP, mp);
    
    if not args.database:
        logger.info("no database file given, setting default database file for webmap");
        args.database = str(pkg_dir.joinpath("noudb"));
    
    logger.debug("initializing answer manager");
    ansmgr = ansm.AnsMgr (
            qmap = mp['qmap'],
            database = args.database,
            mode = ansm.ANS_MODE_NORM,
            pseudo_ans = mp['qmap']['pseudo_ans'].split (','),
            )
    
    logger.debug("initializing a dog to run task");
    libdogs.init_hooks(cookie_hook = getcookie, nav_hook = get_nav);

    dog = simple_dog.SimpleDog(libdogs.preprocess(args), ansmgr, get_nav);


    
    try:
        task = dog._InternalTask(cmd = None, args = args);
        dog.submit(task);

    except KeyboardInterrupt:
        cleanup();

    except BaseException as err:
        cleanup();
        raise err;
    

    return cleanup();


if __name__ == '__main__':

    parser = libdogs.DogCmdParser (fromfile_prefix_chars='@');

    parser.add_argument ('--matno', help = 'Your Matric Number', nargs = "+", action = libdogs.AppendList, dest = libdogs.P_USR);

    parser.add_argument ('--pwd', help = 'Your password', nargs = "+", action = libdogs.AppendList, dest = libdogs.P_PWD);

    parser.add_argument ('--crscode', help = 'Your target course', nargs = "+", action = libdogs.AppendList, dest = libdogs.P_CRSCODE);

    parser.add_argument ('--tma', nargs = "+", help = 'Your target TMA for the chosen course', action = libdogs.AppendList, dest = libdogs.P_TMA);

    parser.add_argument ('--config', help = 'configuration file to use', dest = libdogs.P_WMAP);

    parser.add_argument ('--debug', action = 'store_true', help = 'To enable debug mode')

    parser.add_argument ('--qstdump', default = 'dumpqst.json', help = 'The dump file for questions')

    parser.add_argument ('--database', '-db', help = 'The database to use')

    parser.add_argument ('--noupdatedb', '-nodb', action = 'store_false', dest = 'updatedb', default = True, help = 'Update the database in use')

    parser.add_argument ('--url', help = 'The remote url if no local server', action = libdogs.AppendList, required = True, dest = libdogs.P_URL)


    parser.add_argument ('--cookies', help = 'Website cookies');

    parser.add_argument ('--output', help = "output file format");
    
    pkg_path = sys.argv[0];

    args = parser.parse_args()
    
    main(args, pkg_path);

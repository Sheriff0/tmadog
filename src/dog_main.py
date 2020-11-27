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
import qstwriter
import pathlib
import os

import logging
import libdogs
import simple_dog
import status


def check(pkg_name):
    import uuid
    import hashlib
    import locale
    import os
    import sys

    pkg_dir = pathlib.Path(os.sep.join(str(pathlib.Path(pkg_name).resolve()).split(os.sep)[:-1]));
    mac = bytes(str(uuid.getnode()), encoding = locale.getpreferredencoding());
    hsh = hashlib.sha256(mac);

    fi = pathlib.Path(pkg_dir.joinpath("dog_key.txt"));

    if not fi.exists():
        print("You don't have the required key to use this product.");
        return False;

    else:
        with open(str(fi), "r") as f:
            byt = f.read();
            return byt == hsh.hexdigest();


def mkstat(dog, fi):
    crsreg = {};

    with open(fi, "w") as fp:
        for st in simple_dog.dog_submit_stat(dog):
            arg = st[simple_dog.STAT_ARG];
            crsreg.setdefault(arg[libdogs.P_CRSCODE].lower(), set());
            crsreg[arg[libdogs.P_CRSCODE].lower()].add(arg[libdogs.P_USR].upper());

            line = "" if st[simple_dog.STAT_ST].code >= status.S_INT else "# ";
            line += "--matno %s --pwd %s --crscode %s --tma %s --url %s\n" % (arg[libdogs.P_USR], arg[libdogs.P_PWD], arg[libdogs.P_CRSCODE], arg[libdogs.P_TMA], arg[libdogs.P_URL]);

            line += "# %s %s\n\n" % (st[simple_dog.STAT_ST].msg, str(st[simple_dog.STAT_ST].cause));

            fp.write(line);

    return crsreg;

def main (args, pkg_name):

    pkg_name = pathlib.Path(pkg_name);

    pkg_dir = pkg_name if pkg_name.is_dir() else pkg_name.parent;

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

    lastcookie = args.cookies;

    def getcookie(nav):

        if not args.cookies:
            fi = pathlib.Path(input("""

Please input a cookie file (e.g from the browser)--> """));

            if not isinstance(fi, str) or re.match(r'\s*', fi):
                if not lastcookie:
                    return nav;

                fi = lastcookie;


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
            if not re.match(dog.nav.keys[libdogs.P_USR], cli[libdogs.P_USR], re.I):
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

        crsreg = mkstat(dog, args.stats);

        if args.updatedb:
            dbm.update_hacktab (args.database, ansmgr.iter_cache (),
                    ansmgr.qmap, fp = f);
        if args.debug or args.output:
            arr = []
            for qst in ansmgr.iter_cache ():
               arr.append (qst)

            if args.debug:
                json.dump (arr, f)

            if args.output:
                qstwriter.fromlist(arr, ansmgr.qmap, qstwriter.writeqst(args.output, crsreg));

        if f:
            f.close ()

    if not getattr(args, "stats"):
        logger.info("no stat file given, setting default stat file");
        setattr(args, "stats", str(pkg_dir.joinpath("dog.stat")));


    if not getattr(args, libdogs.P_WMAP):
        logger.info("no config file given, setting default config file for webmap");
        setattr(args, libdogs.P_WMAP, str(pkg_dir.joinpath("nourc")));

    mp = configparser.ConfigParser (interpolation =
        configparser.ExtendedInterpolation ())

    logger.info("reading config file and initializing a webmap");
    mp.read (getattr(args, libdogs.P_WMAP));

    setattr(args, libdogs.P_WMAP, mp);

    if not args.database:
        logger.info("no database file given, setting default database file for webmap");
        args.database = str(pkg_dir.joinpath("noudb"));

    if not args.cache:
        logger.info("no cache dir given, setting default cache directory for quiz");
        args.cache = str(pkg_dir.joinpath("dog_cache"));

    if not args.output:
        logger.info("no output file given, setting default output file for quiz");
        args.output = str(pkg_dir.joinpath("output/{matno}-{c}.txt"));

    pathlib.Path(args.output).parent.resolve().mkdir(parents = True, exist_ok = True);

    logger.debug("initializing answer manager");
    ansmgr = ansm.AnsMgr (
            qmap = mp['qmap'],
            database = args.database,
            mode = ansm.ANS_MODE_NORM,
            pseudo_ans = mp['qmap']['pseudo_ans'].split (','),
            )

    logger.debug("initializing a dog to run task");
    libdogs.init_hooks(cookie_hook = getcookie, nav_hook = get_nav);

    libdogs.CACHE_PAGE_CACHE = args.cache;
    libdogs.CACHE_CACHE_FIRST = args.cache_first;
    libdogs.CACHE_OVERWRITE = args.overwrite;
    dog = simple_dog.SimpleDog(
            libdogs.preprocess(
                args,
                args.exclude if args.exclude else [], # NOTE defaults like
                # this should be in config
                ),
            ansmgr,
            get_nav
            );

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

    parser.add_argument ('--stats', '--summary', help = 'where to write a summary of a run to', dest = "stats");

    parser.add_argument ('--page-cache', help = 'where to write cached pages',
            dest = "cache");

    parser.add_argument("--overwrite", action = "store_true", help = "always update cached pages");

    parser.add_argument("--cache-first", action = "store_true",
            help = "check cached pages before any remote request for the page - not all cached pages will be used.");

    parser.add_argument("--exclude", action = libdogs.AppendList, help =
            "course codes to exclude e.g for NOUN students GST", nargs = "+");

    pkg_path = sys.argv[0];

    args = parser.parse_args()

    if time.time() < 1612137600: # for february 1st.
        main(args, pkg_path);
    else:
        print("this version has expired");

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
import http.server
import qstm
import ansm
import dbm
import iff
import curses
import curses.ascii
import concurrent.futures
import lxml
import scrm
import copy
import pdb
import json
import cloudscraper
import cookie_parse
import dogs
import qstwriter


class CMDLINE_Preprocessor:
    CRSCODE = 'crscode'
    TMA = 'tma'
    URL = 'url'
    WMAP = 'wmap'
    COOKIES = 'cookies'
    SESSION = 'session'

    print = print

    def __init__ (self, **args):
        self.matnos = self.List (args ['matno'])
        self.pwds = self.List (args ['pwd'])
        self.crscodes = self.List (args ['crscode'])
        self.tmas = self.List (args ['tma'])
        self.cookies = self.List (args ['cookies'])
        self.urls = self.List (args ['url'])
        self.wmap = args ['wmap']
        self.UID = self.wmap ['kmap']['matno']
        self.UID1 = self.CRSCODE
        self.UID2 = self.TMA
        self.PWD = self.wmap ['kmap']['pwd']
        self.param = {}
        self.param [self.WMAP] = self.wmap
        self.len = max (len (self.crscodes), len (self.tmas), len (self.matnos))
        self.navtab = scrm.QScrList ()

    def __len__ (self):
        return self.len

    def __iter__ (self):
        yield from self.__next__ ()

    def __next__ (self):

        for i in range (self.len):

            self.param [self.UID] = self.matnos [i]
            self.param [self.PWD] = self.pwds [i]
            self.param [self.TMA] = self.tmas [i]
            self.param [self.URL] = self.urls [i]
            self.param [self.COOKIES] = self.cookies [i]

            if i < len (self.matnos):
                self.param [self.SESSION] = self.mksess (self.param [self.URL],
                        self.param [self.COOKIES])

            y = self.crscodes [i]

            if y == 'all':
                self.print ('No crscode specified')
                yield from self.discovercrs (self.param)
            else:
                self.param [self.CRSCODE]  = y
                yield self.param.copy ()

    def discovercrs (self, param = None):
        param = self.param if not param else param
        try:
            idx = self.navtab.index (param [self.UID], attr = 'refcount')
            nav = self.navtab [idx]

        except ValueError:

            nav = navigation.Navigator (
                    param [self.URL],
                    param [self.WMAP],
                    param, #dangerous maybe
                    session = param [self.SESSION]
                    )

            nav.refcount = param [self.UID]

            self.navtab.append (nav)

        to, tpage = nav ('qst_page')[:-1]
        idx = int (nav.webmap ['qst_page']['indices'].split (',')[-1])
        path = nav.webmap ['qst_page']['path'].split (',')[-1]

        idx += 1

        while True: #crscode discovery
            dt = 'data' if to ['method'] in ('POST', 'post') else 'params'

            m = None

            for k in to.get (dt, {}).values ():
                m = re.search (r'(?P<cs>[A-Za-z]{3})\d{3}(?!\d+)', k)

                if m:
                    break

            if m:
                param [self.CRSCODE] = m.group (0)
                self.print ('Got %s.' % (param [self.CRSCODE],))
                yield param.copy ()

            try:
                rec = iter (navigation.Recipe (path, str (idx), param, tpage,
                    param [self.URL]))

                to = next (rec)
            except TypeError:
                break

            idx += 1

    def mksess (self, url, cookie_file = ''):
        session = None

        if cookie_file:
            with open (cookie_file) as f:
                cookie_str = f.read ()

                session = requests.Session ()
                cookt = cookie_parse.bake_cookies (cookie_str, url)

                session.headers = requests.structures.OrderedDict(
                        (
                            ("Host", None),
                            ("Connection", "keep-alive"),
                            ("Upgrade-Insecure-Requests", "1"),
                            ("User-Agent", cookt [0]['User-Agent']),
                            (
                                "Accept",
                                "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                                ),
                            ("Accept-Language", "en-US,en;q=0.9"),
                            ("Accept-Encoding", "gzip, deflate"),
                            )
                        )

                session.cookies = cookt [1]

        else:
            session = cloudscraper.create_scraper ()


        return session


    class List:
        def __init__ (self, eter):
            self.eter = iter (eter)
            self.list = []
            self.idx = -1

        def __len__ (self):
            self.__getitem__ ()
            return self.idx + 1

        def __getitem__ (self, idx = None):
            idx = int (idx) if idx != None else idx
            if idx == None or idx > self.idx:
                while True:
                    try:
                        x = next (self.eter)
                        self.list.append (x)
                        self.idx += 1

                        if idx != None and idx <= self.idx:
                            break

                    except StopIteration:
                        idx = self.idx
                        break

            idx = self.idx if idx == None else idx
            return self.list [idx] if idx != None and idx >= 0 else None


def main (stdscr, args):


    mp = configparser.ConfigParser (interpolation =
        configparser.ExtendedInterpolation ())

    mp.read (args.wmap)

    args.wmap = mp

    qmap = mp ['qmap']

    curses.start_color ()

    curses.noecho ()

    if not args.cookies:
        args.cookies = ['']

    keys = CMDLINE_Preprocessor (**args.__dict__)


    ansmgr = ansm.AnsMgr (
            qmap = qmap,
            database = args.database,
            mode = ansm.ANS_MODE_NORM,
            pseudo_ans = qmap ['pseudo_ans'].split (','),
            )

    qa_interface = iff.Interface (
            stdscr,
            keys,
            ansmgr
            )

    keys.print = qa_interface.printi
    qa_interface.navtab.extend (keys.navtab)

    qa_interface.doupdate ()

    while True:
        curses.raw ()
        qa_interface ['keypad'] (True)
        qa_interface ['nodelay'] (False)
        qa_interface ['notimeout'] (False)
        c = qa_interface ['getch'] ()

        x = qa_interface (c)

        if x == iff.BREAK:
            break
        elif callable (x):
            if c == curses.KEY_RESIZE:
                curses.update_lines_cols ()
                stdscr.resize (curses.LINES, curses.COLS)
                x (stdscr)


    curses.noraw ()
    curses.echo ()
    curses.endwin ()

    if ansmgr._cur:
        ansmgr.close ()

    f = open (args.qstdump, 'w') if args.debug else None

    if args.updatedb:
        dbm.update_hacktab (args.database, ansmgr.iter_cache (),
                ansmgr.qmap, fp = f)
    elif args.debug or args.output:
        arr = []
        for qst in ansmgr.iter_cache ():
           arr.append (qst)
        
        if args.debug:
            json.dump (arr, f)

        if args.output:
            qstwriter.fromlist(arr, ansmgr.qmap, qstwriter.writeqst(args.output));

    if f:
        f.close ()

    return


if __name__ == '__main__':

    parser = argparse.ArgumentParser ()

    parser.add_argument ('--config', default = 'dogrc', help = 'configuration file to use', dest = 'wmap')

    parser.add_argument ('--debug', action = 'store_true', help = 'To enable debug mode')

    parser.add_argument ('--qstdump', default = 'dumpqst.json', help = 'The dump file for questions')

    parser.add_argument ('--database', '-db', default = 'olddb', help = 'The database to use')

    parser.add_argument ('--noupdatedb', '-nodb', action = 'store_false', dest =
            'updatedb', default = True, help = 'Update the database in use')


    parser.add_argument ('--url', help = 'The remote url if no local server',
            action = 'append', required = True)

    parser.add_argument ('--matno', help = 'Your Matric Number', action = 'append')

    parser.add_argument ('--pwd', help = 'Your password',
            action = 'append')

    parser.add_argument ('--crscode', help = 'Your target course', action = 'append')

    parser.add_argument ('--tma', help = 'Your target TMA for the chosen course', action = 'append')


    parser.add_argument ('--cookies', help = 'Website cookies', action = 'append')

    parser.add_argument ('--output', help = "output file format");

    args = parser.parse_args()


    try:

        stdscr = curses.initscr ()

        main (stdscr, args)

    except BaseException as err:
        curses.endwin ()
        raise err

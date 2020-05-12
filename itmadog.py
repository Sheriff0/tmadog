import time
import math
import unittest
import argparse
import sys
import urllib.parse
import re
import tmadog_server
import requests
import threading
from navigation import Navigation
import configparser
import http.server
from qstmgt import QstMgt
from ansmgt import AnsMgt
import dbmgt
import curses
import curses.ascii
import concurrent.futures
import lxml
import qscreen
import copy
import pdb
import json
import cloudscraper
import cookie_parse

BREAK = -1

CONT = 1

TOP = 0b00001
BOTTOM = 0b00010
CAPTURED = 0b00100
BELOW = 0b01000
ABOVE = 0b10000
UNCAPTURED = BELOW | ABOVE

PRT_PRINT_QST = 0b001
PRT_PRINT_CHOICES = 0x80
PRT_KEEPLINE = 0b010
PRT_KEEPCUR = 0b0100

class MPCT_Preprocessor:
    CRSCODE = 'crscode'
    TMA = 'tma'
    URL = 'url'
    WMAP = 'wmap'
    COOKIES = 'cookies'

    def __init__ (self, **args):
        self.matnos = args ['matno']
        self.pwds = args ['pwd']
        self.crscodes = args ['crscode']
        self.tmas = args ['tma']
        self.cookies = args ['cookies']
        self.urls = args ['url']
        self.wmap = args ['wmap']
        self.UID = self.wmap ['kmap']['matno']
        self.UID1 = self.CRSCODE
        self.UID2 = self.TMA
        self.PWD = self.wmap ['kmap']['pwd']
        self.param = {}
        self.param [self.WMAP] = self.wmap
        self.len = max (len (self.crscodes), len (self.tmas), len (self.matnos))

    def __len__ (self):
        return self.len

    def __iter__ (self):
        yield from self.__next__ ()

    def __next__ (self):

        for i in range (self.len):

            try:
                self.param [self.UID] = self.matnos [i]
                self.param [self.PWD] = self.pwds [i]
                self.param [self.CRSCODE] = self.crscodes [i]
                self.param [self.TMA] = self.tmas [i]
                self.param [self.URL] = self.urls [i]
                self.param [self.COOKIES] = self.cookies [i]

            except IndexError:
                try:
                    self.param [self.CRSCODE] = self.crscodes [i]
                    self.param [self.TMA] = self.tmas [i]
                    self.param [self.URL] = self.urls [i]
                    self.param [self.COOKIES] = self.cookies [i]

                except IndexError:
                    pass

            finally:
                yield self.param.copy ()



class Interface:
    def __init__ (self, stdscr, keys, amgr):
        self.scr_mgr = qscreen.QscrMuxer (stdscr, keys)
        self.keys = keys
        self.amgr = amgr
        curses.curs_set (0)
        self.pq = []
        self.pqlen = 0
        self.stdscr = stdscr
        self.boot ()
        self.update_qscr ()

    def __getitem__ (self, attr):
        return getattr (self.scr_mgr ['qscr'], attr)


    def boot (self, qscr = None):
        if not hasattr (self, 'navtab'):
            self.navtab = qscreen.QScrList ()

        if not qscr:
            qscr = self.scr_mgr

        if 'nav' not in qscr or 'qmgr' not in qscr or not qscr ['nav'] or not qscr ['qmgr']:
            if 'nav' not in qscr or not qscr ['nav']:

                try:
                    idx = self.navtab.index (qscr [self.keys.UID], attr = 'refcount')
                    qscr ['nav'] = self.navtab [idx]

                except ValueError:

                    nav = Navigation.Navigator (
                            qscr [self.keys.URL],
                            qscr [self.keys.WMAP],
                            qscr, #dangerous maybe
                            session = self.mksess (qscr [self.keys.URL], qscr [self.keys.COOKIES])
                            )

                    qscr ['nav'] = nav

                    nav.refcount = qscr [self.keys.UID]

                    self.navtab.append (nav)



            to, fro = qscr ['nav'] ('qst_page')[:-1]
            qscr ['qmgr'] = QstMgt.QstMgr (
                    matno = qscr [self.keys.UID],
                    crscode = qscr [self.keys.CRSCODE],
                    tma = qscr [self.keys.TMA],
                    fargs = copy.deepcopy (to),
                    stop = 10,
                    url = fro.url,
                    qmap = qscr [self.keys.WMAP]['qmap'],
                    session = qscr ['nav'].session

                    )

            qscr ['qline'] = 0
            qscr ['optmap'] = []
            qscr ['pqidx'] = None
            qscr ['lpqidx'] = None
            qscr ['qst'] = None
            qscr ['qmode'] = False
            qscr ['qmgr'].interactive = True

        return qscr ['qmgr']


    def __call__ (self, key):

        args = bytearray ()
        c = key
        self ['keypad'] (True)
        self ['nodelay'] (False)
        self ['notimeout'] (True)

        while True:
            comm = self._get_cmd (c)
            if comm:
                return comm (args) if args else comm ()

            elif c >= 0 and c <= 255:
                args.append (c)
                c = self ['getch'] ()

            else:
                return



    def _get_cmd (self, key):
        cmd = (getattr (self, k) for k in type (self).__dict__ if re.search
                (r'(?<!\d)' + str (key) + r'(?!\d)', k))

        try:
            comm = next (cmd)
            return comm

        except StopIteration:
            return None


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


    def key_left260 (self, subtrahend = b'1'):
        if self.scr_mgr ['lpqidx'] != None and self.scr_mgr ['pqidx'] != None and self.scr_mgr ['qmode'] and self.pq:

            if not subtrahend.isdigit ():
                return

            subtrahend = int (subtrahend.decode())

            l = self.amgr (*self.pq [self.scr_mgr ['lpqidx']])

            self.scr_mgr ['pqidx'] -= subtrahend

            if 0 <= self.scr_mgr ['pqidx'] < self.pqlen:
                    p = self.amgr (*self.pq [self.scr_mgr ['pqidx']])

                    if p and l:
                        self.update_qscr (self.amgr.download (p, l))

                    else:
                        pass #pdb.set_trace ()

            elif self.scr_mgr ['pqidx'] < 0:
                self.scr_mgr ['pqidx'] = 0


    def key_right261 (self, addend = b'1'):
        if self.scr_mgr ['lpqidx'] != None and self.scr_mgr ['pqidx'] != None and self.scr_mgr ['qmode'] and self.pq:
            l = self.amgr (*self.pq [self.scr_mgr ['lpqidx']])

            if not addend.isdigit ():
                return

            addend = int (addend.decode())

            self.scr_mgr ['pqidx'] += addend

            if 0 <= self.scr_mgr ['pqidx'] < self.pqlen:
                p = self.amgr (*self.pq [self.scr_mgr ['pqidx']])

                if p and l:
                    self.update_qscr (self.amgr.download (p, l))

                else:
                    pass #pdb.set_trace ()

            elif self.scr_mgr ['pqidx'] >= self.pqlen:
                self.scr_mgr ['pqidx'] = self.pqlen

                if l != self.scr_mgr ['qst']:
                    self.update_qscr (self.amgr.download (l, self.scr_mgr ['qst']))


    def key_up259 (self, subtrahend = b'1'):
        if not subtrahend.isdigit ():
            return

        subtrahend = int (subtrahend.decode())

        if self.scr_mgr ['qmode'] and self.scr_mgr ['optmap']:
            cur = self.scr_mgr ['qscr'].getyx ()
            n = [i for i,t in enumerate (self.scr_mgr ['optmap']) if t[0] == cur [0]]

            if not n:
                return

            try:
                if (n [0] - subtrahend) < 0:
                        raise IndexError (n [0] - subtrahend)


                t = self.scr_mgr ['optmap'] [n [0]]
                vis, trange = self.visibility (t)

                if vis & UNCAPTURED:
                    offset = t[0] - (self.scr_mgr ['qline'] + self.scr_mgr.scrdim[0] - 1)
                    self.scr_mgr ['qline'] += offset

                elif vis & TOP:

                    t = n [0] - subtrahend

                    t = self.scr_mgr ['optmap'] [t]

                    vis, trange = self.visibility (t)
                    if vis & ABOVE:
                        self.scr_mgr ['qline'] = trange [-1]

                else:
                    self.scr_mgr ['qline'] -= subtrahend


            except IndexError:
                t = self.scr_mgr ['optmap'] [0]
                vis, trange = self.visibility (t)
                if vis & ABOVE:
                    self.scr_mgr ['qline'] = trange [-1]

                else:
                    self.scr_mgr ['qline'] -= subtrahend

            self.paint (undo = True)

            self.scr_mgr ['qscr'].move (t[0], 0)
            self.paint ()

        elif not self.scr_mgr ['qmode']:
            self.scr_mgr ['qline'] -= subtrahend


        if self.scr_mgr ['qline'] < 0:
            self.scr_mgr ['qline'] = 0

        self.scr_mgr ['qscr'].noutrefresh (self.scr_mgr ['qline'], 0, self.scr_mgr.scord[0], self.scr_mgr.scord [1],
        (self.scr_mgr.scrdim [0] + self.scr_mgr.scord [0]) - 1, (self.scr_mgr.scrdim [1] + self.scr_mgr.scord
            [1]) - 1)


    def key_down258 (self, addend = b'1'):
        if not addend.isdigit ():
            return

        addend = int (addend.decode())

        if self.scr_mgr ['qmode'] and self.scr_mgr ['optmap']:
            cur = self.scr_mgr ['qscr'].getyx ()
            n = [i for i,t in enumerate (self.scr_mgr ['optmap']) if t[0] == cur [0]]

            if not n:
                return

            try:
                self.scr_mgr ['optmap'] [n [0] + addend]
                t = self.scr_mgr ['optmap'] [n [0]]
                vis, trange = self.visibility (t)

                if vis & ABOVE:
                    self.scr_mgr ['qline'] = trange [-1]

                elif vis & BOTTOM:
                    t = self.scr_mgr ['optmap'] [n [0] + addend]

                    vis, trange = self.visibility (t)
                    if vis & BELOW:
                        self.scr_mgr ['qline'] = trange [0]


                else:
                    self.scr_mgr ['qline'] += addend

                tl = self.scr_mgr ['optmap'] [-1]
                visl, trangel = self.visibility (tl)

            except IndexError:
                t = tl = self.scr_mgr ['optmap'] [-1]
                vis, trange = visl, trangel = self.visibility (t)

                if vis & UNCAPTURED:
                    self.scr_mgr ['qline'] = trange [0]

                else:
                    self.scr_mgr ['qline'] += addend

            bot_scry = (self.scr_mgr ['qline'] + self.scr_mgr.scrdim [0]) - 1
            if bot_scry > trangel [-1]:
                self.scr_mgr ['qline'] -= bot_scry - trangel [-1]

            self.paint (undo = True)

            self.scr_mgr ['qscr'].move (t[0], 0)
            self.paint ()


        elif not self.scr_mgr ['qmode']:
            if hasattr (self, 'msgyx') and self.msgyx:
                self.scr_mgr ['qline'] += addend
                vis, trange = self.visibility (self.msgyx)

                bot_scry = (self.scr_mgr ['qline'] + self.scr_mgr.scrdim [0]) - 1

                if bot_scry > trange [-1]:
                    self.scr_mgr ['qline'] -= bot_scry - trange [-1]


        self.scr_mgr ['qscr'].noutrefresh (self.scr_mgr ['qline'], 0, self.scr_mgr.scord[0], self.scr_mgr.scord [1],
        (self.scr_mgr.scrdim [0] + self.scr_mgr.scord [0]) - 1, (self.scr_mgr.scrdim [1] + self.scr_mgr.scord
            [1]) - 1)


    def visibility (self, coord):
        flags = 0

        topy = coord [0]

        boty = math.floor (coord [1] / self.scr_mgr.scrdim [1]) + topy


        bot_scry = (self.scr_mgr ['qline'] + self.scr_mgr.scrdim [0]) - 1

        top_scry = self.scr_mgr ['qline']

        txt_range = (topy, boty)

        if bot_scry >= boty >= top_scry:
            flags |= BOTTOM

        if top_scry <= topy <= bot_scry:
            flags |= TOP

        if top_scry >= topy and bot_scry <= boty:
            flags |= CAPTURED

        if boty < top_scry:
            flags |= ABOVE

        if topy > bot_scry:
            flags |= BELOW

        return (flags, txt_range)


    def enter10 (self, c = False):

        if self.scr_mgr ['qmode'] and self.scr_mgr ['qst']:
            if c == False:
                c = self ['instr'] (len (self.scr_mgr ['qmgr'].pseudos [0]))

            c = c.decode ()

            self.scr_mgr ['qst'] [self.scr_mgr ['qmgr'].qmap ['ans']] = c

            try:
                e = self.scr_mgr ['qmgr'].submit (self.scr_mgr ['qst'])

                x = re.search (r'(?P<mark>[01])\s*' + self.scr_mgr ['nav'].webmap ['fb']['on_qst_submit'].strip (), self.scr_mgr ['qmgr'].sres.text, re.I)

                if x:
                    self.amgr.check (self.scr_mgr ['qst'], int (x.group ('mark')), e)
                return self.message (self.scr_mgr ['qmgr'].sres)

            except:

                self.scr_mgr ['qst'] = None
                return self.update_qscr ()

        else:

            post_fetch_h = self.update_qscr
            post_fetch_arg = ()

            try:
                qst = self.scr_mgr ['qmgr'].fetch (timeout = (30.5, 60))

                if qst and isinstance (qst, lxml.html.FieldsDict):

                    x = copy.deepcopy (qst)

                    x = self.amgr.answer (x)

                    if x and x != self.amgr.NOANSWER and qst [self.scr_mgr ['qmgr'].qmap ['qid']] == x [self.scr_mgr ['qmgr'].qmap ['qid']]:
                        qst = x

                    self.pq.append ((qst [self.scr_mgr ['qmgr'].qmap ['crscode']], qst
                        [self.scr_mgr ['qmgr'].qmap ['qid']]))

                    self.pqlen += 1

                    self.scr_mgr ['lpqidx'] = self.pqlen - 1
                    self.scr_mgr ['pqidx'] = self.scr_mgr ['lpqidx']

                    self.scr_mgr ['qmode'] = True

                    post_fetch_arg = (qst,)
                    curses.flushinp() #For safety

                else:
                    post_fetch_h = self.message
                    post_fetch_arg = (self.scr_mgr ['qmgr'].qres,)

            except:
                post_fetch_arg = (None,)
                self.scr_mgr ['qst'] = None
            return post_fetch_h (*post_fetch_arg)


    def message (self, res):

        y = lxml.html.fromstring (res.text).text_content ()

        self.scr_mgr ['qscr'].clear ()

        self.scr_mgr ['qscr'].addstr (0, 0, y)

        self.msgyx = [0]

        self.msgyx.append ((self.scr_mgr ['qscr'].getyx ()[0] + 1) * self.scr_mgr.scrdim
                [1])

        self.scr_mgr ['qline'] = 0

        self.scr_mgr ['qscr'].noutrefresh (self.scr_mgr ['qline'], 0, self.scr_mgr.scord[0], self.scr_mgr.scord [1],
                (self.scr_mgr.scrdim [0] + self.scr_mgr.scord [0]) - 1, (self.scr_mgr.scrdim [1] + self.scr_mgr.scord
                    [1]) - 1)

        self.scr_mgr ['qmode'] = False


    def update_qscr (
            self,
            qst = None,
            flags = PRT_PRINT_QST | PRT_PRINT_CHOICES,
            qpaint = curses.A_NORMAL,
            opaint = curses.A_NORMAL,
            apaint = curses.A_BLINK
            ):

        if qst:
            self.scr_mgr ['qst'] = qst

        elif not self.scr_mgr ['qst']:
            self.scr_mgr ['qline'] = 0
            self.scr_mgr ['qscr'].clear ()
            self.scr_mgr ['qscr'].addstr (0, 0, 'Hit Enter to start')
            self.scr_mgr ['qscr'].noutrefresh (self.scr_mgr ['qline'], 0, self.scr_mgr.scord[0], self.scr_mgr.scord [1],
                    (self.scr_mgr.scrdim [0] + self.scr_mgr.scord [0]) - 1, (self.scr_mgr.scrdim [1] + self.scr_mgr.scord
                        [1]) - 1)
            return



        if not (PRT_KEEPLINE & flags):
            self.scr_mgr ['qline'] = 0
            fcur = None

        else:
            fcur = self.scr_mgr ['qscr'].getyx ()

        if (PRT_PRINT_CHOICES & flags) and (PRT_PRINT_QST & flags):
            self.scr_mgr ['qscr'].clear ()


        if PRT_PRINT_QST & flags:
            if isinstance (self.scr_mgr ['qst'] [self.scr_mgr ['qmgr'].qmap ['qn']], int):
                self.scr_mgr ['qscr'].addch (self.scr_mgr ['qmgr'].pseudos [i])
                pre = ''
            else:
                pre = str (self.scr_mgr ['qst'] [self.scr_mgr ['qmgr'].qmap ['qn']]) + '. '

            self.scr_mgr ['qscr'].addstr (0, 0, pre + self.scr_mgr ['qst'] [self.scr_mgr ['qmgr'].qmap ['qdescr']].strip () + '\n\n', qpaint)


        obitmap = 1 if PRT_PRINT_CHOICES & flags else (flags & 0x7f) >> 3

        if obitmap:
            ol = len (self.scr_mgr ['optmap'])

            for opt in ['opt' + chr (97 + i) for i in range (len (self.scr_mgr ['qmgr'].pseudos))]:
                if obitmap & 1:
                    i = (ord (opt[-1]) & 0x1f) - 1
                    df = ol - i

                    if df <= 0:
                        self.scr_mgr ['optmap'].extend (range (abs (df) + 1))
                        ol += abs (df + 1)

                    if PRT_PRINT_QST & flags:
                        w = self.scr_mgr ['qscr'].getyx ()
                    else:
                        if df > 0:
                            w = self.scr_mgr ['optmap'][i]
                        else:
                            w = self.scr_mgr ['qscr'].getyx ()

                    y, x = w[0], 0

                    if isinstance (self.scr_mgr ['qmgr'].pseudos [i], int):
                        self.scr_mgr ['qscr'].addch (self.scr_mgr ['qmgr'].pseudos [i])
                        pre = ''
                    else:
                        pre = self.scr_mgr ['qmgr'].pseudos [i] + ': '


                    self.scr_mgr ['qscr'].addstr (y, x, pre + self.scr_mgr ['qst'] [self.scr_mgr ['qmgr'].qmap [opt]].strip ())

                    if PRT_PRINT_QST & flags:
                        cur = self.scr_mgr ['qscr'].getyx ()
                        l = (cur [0] - w[0]) * (self.scr_mgr.scrdim [1]) + cur [1]

                    else:
                        l = self.scr_mgr ['optmap'][i][1]

                    self.scr_mgr ['optmap'][i] = [
                        w[0],
                        l,
                        self.scr_mgr ['qmgr'].pseudos [i] if isinstance (self.scr_mgr ['qmgr'].pseudos [i], int) else None,
                        opaint
                        ]

                    self.scr_mgr ['qscr'].addch ('\n')

                if not PRT_PRINT_CHOICES & flags:
                    obitmap >>= 1



            if not self.scr_mgr ['optmap']:
                pass #NOTE: Draw a textbox for fill-in-the-gap answer


            elif self.scr_mgr ['qst'] [self.scr_mgr ['qmgr'].qmap ['qid']] != 'error':

                a = self.scr_mgr ['qst'] [self.scr_mgr ['qmgr'].qmap ['ans']]

                if a:
                    i = self.scr_mgr ['qmgr'].pseudos.index (a)

                    self.scr_mgr ['optmap'] [i][-1] = apaint

                else:
                    i = 0

            else:
                    i = 0

            self.paint (self.scr_mgr ['optmap'] [i])

        if PRT_KEEPCUR & flags:
            self.scr_mgr ['qscr'].move (*fcur)

        self.scr_mgr ['qscr'].noutrefresh (self.scr_mgr ['qline'], 0, self.scr_mgr.scord[0], self.scr_mgr.scord [1],
                (self.scr_mgr.scrdim [0] + self.scr_mgr.scord [0]) - 1, (self.scr_mgr.scrdim [1] + self.scr_mgr.scord
                    [1]) - 1)

        return

    def ctrl_l12 (self, *args):
        if self.scr_mgr ['qmode'] and self.scr_mgr ['qst']:
            curses.flash ()
            self.update_qscr ()

    def ctrl_c3 (self, *args):
        return BREAK

    def key_resize410 (self):
        curses.update_lines_cols ()

        self.stdscr.resize (curses.LINES, curses.COLS)

        r = self.scr_mgr.resize (self.stdscr)
        if r and r != -1:
            for scr, inc in r:
                self.update_qscr (
                        scr ['qst'] if not inc else None,
                        flags = PRT_PRINT_CHOICES | PRT_PRINT_QST | PRT_KEEPLINE if inc else PRT_PRINT_QST | PRT_PRINT_CHOICES)

            return inc

        else:
            return r

    def ctrl_w23 (self, offset = b'1'):
        if not offset.isdigit ():
            return

        offset = int (offset.decode ())
        self ['keypad'] (True)
        c = self ['getch'] ()

        if c == curses.KEY_UP or c == curses.KEY_LEFT:
            self.scr_mgr.scroll (-offset)
            self.boot ()
            self.update_qscr (flags = PRT_KEEPLINE)

        elif c == curses.KEY_DOWN or c == curses.KEY_RIGHT:
            self.scr_mgr.scroll (offset)
            self.boot ()
            self.update_qscr (flags = PRT_KEEPLINE)


    def paint (self, t = None, color = curses.A_BOLD | curses.A_REVERSE,
            undo = False, optmap = None):

        if t == None:
            optmap = optmap if optmap else self.scr_mgr ['optmap']

            if not optmap:
                return

            cur = self.scr_mgr ['qscr'].getyx ()

            t = [x for x in optmap if x [0] == cur [0]]

            if not t:
                return

            else:
                t = t[0]

        c = divmod (t [1], self.scr_mgr.scrdim [1])
        l = t [0]

        x = c[0]

        while x:
            self.scr_mgr ['qscr'].chgat (l, 0, (color) if not undo
                    else t[-1])
            l += 1
            x -= 1

        self.scr_mgr ['qscr'].chgat (l, 0, c [1], (color) if not undo
                else t [-1])

        if t [2]:
            self.scr_mgr ['qscr'].addch (t[0], 0, t[2])

        self.scr_mgr ['qscr'].move (t[0], 0)

    def ctrl_r18 (self):
        if self.scr_mgr ['qmode'] and self.scr_mgr ['qst']:
            qst = self.scr_mgr['qst'].copy ()

            for k, v in self.scr_mgr ['nav'].webmap ['retros'].items ():
                if k not in qst:
                    break
                qst [k] = v

            return self.update_qscr (qst)

    def ctrl_x24 (self, keep_prev = True):
        return
        if not hasattr (self, 'form'):
            self.form = {
                    self.scr_mgr ['qmgr'].qmap ['qdescr']: 'Please fill in below:',
                    self.scr_mgr ['qmgr'].qmap ['qn']: 'FORM',
                    }

            self.form_fields = []

            for i, k in enumerate (self.keys.param):
                self.form_fields.append (k)
                self.form [self.scr_mgr ['qmgr'].qmap ['opt' + chr (i)]] = ''
                self.form [k] = self.keys.param [k]

        self.scr_mgr ['qmgr'].pseudos, self.form_fields = self.form_fields,  self.scr_mgr ['qmgr'].pseudos


    def ctrl_s19 (self):
        self ['timeout'] (5000)
        c = self ['getch'] ()
        c = '' if c == -1 else chr (c & 0xff)
        self.scr_mgr ['qst'] = self.scr_mgr ['qst'].copy ()
        self ['timeout'] (-1)
        return self.enter10 (c)

    def keys_minus45 (self, subtrahend = None):
        if self.scr_mgr ['qmode'] and self.scr_mgr ['qst']:
            if not subtrahend or not subtrahend.isdigit ():
                subtrahend = 1
            else:
                subtrahend = int (subtrahend.decode())

            qst = self.scr_mgr ['qst'].copy ()
            n = math.trunc (int (qst [self.scr_mgr ['qmgr'].qmap ['qn']] + '0') / 10) - subtrahend

            qst [self.scr_mgr ['qmgr'].qmap ['qn']] = str (n)

            self.update_qscr (qst, flags = PRT_PRINT_CHOICES | PRT_PRINT_QST | PRT_KEEPLINE)

    def key_plus43 (self, addend = None):
        if self.scr_mgr ['qmode'] and self.scr_mgr ['qst']:
            if not addend or not addend.isdigit ():
                addend = 1
            else:
                addend = int (addend.decode())

            qst = self.scr_mgr ['qst'].copy ()
            n = math.trunc (int (qst [self.scr_mgr ['qmgr'].qmap ['qn']] + '0') / 10) + addend

            qst [self.scr_mgr ['qmgr'].qmap ['qn']] = str (n)

            self.update_qscr (qst, flags = PRT_PRINT_CHOICES | PRT_PRINT_QST | PRT_KEEPLINE)


    def key_asterik42 (self, addend = None):
        if self.scr_mgr ['qmode'] and self.scr_mgr ['qst']:
            if not addend or not addend.isdigit ():
                addend = 1
            else:
                addend = int (addend.decode())

            qst = self.scr_mgr ['qst'].copy ()
            n = math.trunc (int (qst [self.scr_mgr ['qmgr'].qmap ['score']] + '0') / 10) + addend

            qst [self.scr_mgr ['qmgr'].qmap ['score']] = str (n)

            self.update_qscr (qst, flags = PRT_PRINT_CHOICES | PRT_PRINT_QST | PRT_KEEPLINE)


    def keys_fslash47 (self, subtrahend = None):
        if self.scr_mgr ['qmode'] and self.scr_mgr ['qst']:
            if not subtrahend or not subtrahend.isdigit ():
                subtrahend = 1
            else:
                subtrahend = int (subtrahend.decode())

            qst = self.scr_mgr ['qst'].copy ()
            n = math.trunc (int (qst [self.scr_mgr ['qmgr'].qmap ['score']] + '0') / 10) - subtrahend

            qst [self.scr_mgr ['qmgr'].qmap ['score']] = str (n)

            self.update_qscr (qst, flags = PRT_PRINT_CHOICES | PRT_PRINT_QST | PRT_KEEPLINE)


    def key_caret94 (self, crscode = bytearray ()):
        if self.scr_mgr ['qmode'] and self.scr_mgr ['qst']:
            crscode = crscode.decode()

            qst = {}

            for k,v in self.scr_mgr ['qst'].copy ().items ():
                if isinstance (v, str):
                    v = re.sub (r'(?P<cs>' + self.scr_mgr ['crscode'] + ')',
                            self.scr_mgr ['qmgr']._copycase (crscode), v, flags =
                            re.I)
                qst [k] = v

            self.update_qscr (qst, flags = PRT_PRINT_CHOICES | PRT_PRINT_QST | PRT_KEEPLINE)

    def key_qmark33 (self, matno = bytearray ()):
        if self.scr_mgr ['qmode'] and self.scr_mgr ['qst']:
            matno = matno.decode()

            if not matno:
                matno = 'Nou123456789'

            qst = {}

            for k, v in self.scr_mgr ['qst'].copy ().items ():
                if isinstance (v, str):
                    v = re.sub (r'(?P<cs>' + self.scr_mgr [self.keys.UID] + ')',
                            self.scr_mgr ['qmgr']._copycase (matno), v, flags =
                            re.I)
                qst [k] = v

            self.update_qscr (qst, flags = PRT_PRINT_QST | PRT_KEEPLINE | PRT_KEEPCUR, qpaint = curses.A_DIM)


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

    keys = MPCT_Preprocessor (**args.__dict__)

    ansmgr = AnsMgt.AnsMgr (
            qmap = qmap,
            database = args.database,
            mode = AnsMgt.AnsMgr.ANS_MODE_HACK | AnsMgt.AnsMgr.ANS_MODE_NORM,
            pseudo_ans = qmap ['pseudo_ans'].split (','),
            interactive = False,
            )

    qa_interface = Interface (
            stdscr,
            keys,
            ansmgr
            )

    curses.doupdate ()

    while True:
        curses.raw ()
        qa_interface ['keypad'] (True)
        qa_interface ['nodelay'] (False)
        qa_interface ['notimeout'] (True)
        c = qa_interface ['getch'] ()

        c = qa_interface (c)
        curses.doupdate ()

        if c == BREAK:
            break


    curses.noraw ()
    curses.echo ()
    curses.endwin ()

    if ansmgr._cur:
        ansmgr.close ()

    f = open (args.qstdump, 'w') if args.debug else None

    if args.updatedb:
        dbmgt.DbMgt.update_hacktab (args.database, ansmgr.iter_cache (),
                ansmgr.qmap, fp = f)
    elif args.debug:
        arr = []
        for qst in ansmgr.iter_cache ():
           arr.append (qst)

        json.dump (arr, f)

    if f:
        f.close ()

    return


if __name__ == '__main__':

    parser = argparse.ArgumentParser ()

    parser.add_argument ('--config', default = 'dogrc', help = 'configuration file to use', dest = 'wmap')

    parser.add_argument ('--debug', action = 'store_true', help = 'To enable debug mode')

    parser.add_argument ('--qstdump', default = 'dumpqst.json', help = 'The dump file for questions')

    parser.add_argument ('--database', '-db', default = 'pg/olddb', help = 'The database to use')

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

    args = parser.parse_args()


    try:

        stdscr = curses.initscr ()

        main (stdscr, args)

    except BaseException as err:
        curses.endwin ()
        raise err


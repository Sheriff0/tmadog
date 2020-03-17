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
import cfscrape
import concurrent.futures
import lxml
import qscreen
import copy

BREAK = 0

CONT = 1

TOP = 1

BOTTOM = 0

class MPCT_Preprocessor:
    CRSCODE = 'crscode'
    TMA = 'tma'
    URL = 'url'
    WMAP = 'wmap'

    def __init__ (self, **args):
        self.matnos = args ['matno']
        self.pwds = args ['pwd']
        self.crscodes = args ['crscode']
        self.tmas = args ['tma']
        self.urls = args ['url']
        self.wmap = args ['wmap']
        self.MATNO = self.wmap ['kmap']['matno']
        self.PWD = self.wmap ['kmap']['pwd']
        self.param = {}
        self.param [self.WMAP] = self.wmap

    def __len__ (self):
        return len (self.matnos)

    def __iter__ (self):
        yield from self.__next__ ()

    def __next__ (self):

        for i, m in enumerate (self.matnos):
            self.param [self.MATNO] = m

            try:
                self.param [self.PWD] = self.pwds [i]
                self.param [self.CRSCODE] = self.crscodes [i]
                self.param [self.TMA] = self.tmas [i]
                self.param [self.URL] = self.urls [i]

            except IndexError:
                pass

            finally:
                yield self.param



class Interface:
    def __init__ (self, scr_mgr, amgr):
        self.scr_mgr = scr_mgr
        self.amgr = amgr
        curses.curs_set (0)
        self.qst = None
        self.qmode = True
        self.pq = []
        self.pqlen = 0
        self.update_qscr ()

    def resize_screen (self, screen):
        r = self.scr_mgr.resize (screen)
        if r and r != -1:
            for scr in r:
                if scr.pqidx >= 0:
                    self.key_right261 (True)
                else:
                    self.qst = None
                    self.update_qscr ()

    def __getitem__ (self, attr):
        return self.scr_mgr [attr]

    def __call__ (self, key):
        cmd = (getattr (self, k) for k in type (self).__dict__ if re.search
                (r'(?<!\d)' + str (key) + r'(?!\d)', k))
        try:
            return next (cmd)()
        except StopIteration:
            raise NotImplementedError ('code %d not available' % (key,), key)

    def key_left260 (self, refresh = False):
        if self.qmode:
            if self.pq:
                l = self.amgr (*self.pq [self.scr_mgr.lpqidx])

                if not refresh:
                    self.scr_mgr.pqidx -= 1
                
                if 0 <= self.scr_mgr.pqidx < self.pqlen:
                        p = self.amgr (*self.pq [self.scr_mgr.pqidx])

                        if p and l:
                            self.update_qscr (self.amgr.download (p, l))

                elif self.scr_mgr.pqidx < 0:
                    self.scr_mgr.pqidx = 0


    def key_right261 (self, refresh = False):
        if self.qmode and self.pq:
            l = self.amgr (*self.pq [self.scr_mgr.lpqidx])

            if not refresh:
                self.scr_mgr.pqidx += 1
            
            if 0 <= self.scr_mgr.pqidx < self.pqlen:
                p = self.amgr (*self.pq [self.scr_mgr.pqidx])

                if p and l:
                    self.update_qscr (self.amgr.download (p, l))

            elif self.scr_mgr.pqidx >= self.pqlen:
                if (self.scr_mgr.pqidx - self.scr_mgr.lpqidx) == 1 and not refresh:
                    self.scr_mgr.pqidx = self.pqlen - 1
                    return 

                self.scr_mgr.pqidx = self.pqlen - 1

                if l:
                    self.update_qscr (l)


    def key_up259 (self):
        if self.qmode and self.optmap:
            cur = self.scr_mgr.qscr.getyx ()
            n = [i for i,t in enumerate (self.optmap) if t[0] == cur [0]]

            if not n:
                return

            try:
                t = n [0] - 1
                
                if t < 0:
                    raise IndexError (t)
                t = self.optmap [t]

                if self.isseen (self.optmap [n [0]], TOP):
                    self.paint (undo = True)


                    if self.isseen (t, TOP):
                        pass

                    elif self.isseen (t, BOTTOM):
                        self.scr_mgr.qline -= 1

                    else:
                        self.scr_mgr.qline -= t[0]

                    self.scr_mgr.qscr.move (t[0], 0)

                else:
                    self.scr_mgr.qline -= 1

                self.paint ()

            except IndexError:
                if self.isseen ((0, self.scr_mgr.scrdim[1] - 1), TOP):
                    pass
                else:
                    self.scr_mgr.qline -= 1

        elif not self.qmode:
            if not self.isseen (self.msgyx, TOP):
                self.scr_mgr.qline -= 1


        self.scr_mgr.qscr.noutrefresh (self.scr_mgr.qline, 0, self.scr_mgr.scord[0], self.scr_mgr.scord [1],
        (self.scr_mgr.scrdim [0] + self.scr_mgr.scord [0]) - 1, (self.scr_mgr.scrdim [1] + self.scr_mgr.scord
            [1]) - 1)


    def key_down258 (self):
        if self.qmode and self.optmap:
            cur = self.scr_mgr.qscr.getyx ()
            n = [i for i,t in enumerate (self.optmap) if t[0] == cur [0]]

            if not n:
                return

            try:
                t = self.optmap [n [0] + 1]

                if self.isseen (self.optmap [n [0]]):
                    self.paint (undo = True)


                    if self.isseen (t, 0):
                        pass

                    elif self.isseen (t, 1):
                        self.scr_mgr.qline += 1

                    else:
                        offset = t[0] - (self.scr_mgr.qline + self.scr_mgr.scrdim[0] - 1)
                        self.scr_mgr.qline += offset if offset >= 0 else 1

                    self.scr_mgr.qscr.move (t[0], 0)

                elif self.isseen (self.optmap [n [0]], 1):
                    self.scr_mgr.qline += 1

                else:
                    self.scr_mgr.qline += 1


                self.paint ()

            except IndexError:
                if self.isseen (self.optmap [n [0]]):
                    pass
                else:
                    self.scr_mgr.qline += 1


        elif not self.qmode:
            if not self.isseen (self.msgyx, BOTTOM):
                self.scr_mgr.qline += 1

        self.scr_mgr.qscr.noutrefresh (self.scr_mgr.qline, 0, self.scr_mgr.scord[0], self.scr_mgr.scord [1],
        (self.scr_mgr.scrdim [0] + self.scr_mgr.scord [0]) - 1, (self.scr_mgr.scrdim [1] + self.scr_mgr.scord
            [1]) - 1)
                        

    def isseen (self, coord, dir = TOP):
        if dir == BOTTOM:
            x = math.floor (coord [1] / self.scr_mgr.scrdim [1]) + coord [0]
            y = (self.scr_mgr.qline + self.scr_mgr.scrdim [0]) - 1
            return y >= x >= self.scr_mgr.qline
        
        elif dir == TOP:
            x = coord [0]
            y = (self.scr_mgr.qline + self.scr_mgr.scrdim [0]) - 1
            return self.scr_mgr.qline <= x <= y


    def enter10 (self):

        if self.qmode and self.qst: 
            c = chr (self ['inch'] () & 0xff)
            self.qst [self.scr_mgr.qmgr.qmap ['ans']] = c
           
            e = self.scr_mgr.qmgr.submit (self.qst)

            self.qmode = False

            if hasattr (self.scr_mgr.qmgr, 'sres'):
                y = lxml.html.fromstring (self.scr_mgr.qmgr.sres.text).text_content ()

                x = re.search (r'(?P<mark>[01])\s+mark for question', y, re.I)

                if self.qst [self.scr_mgr.qmgr.qmap ['qid']] != 'error' and x:
                    self.amgr.check (self.qst, int (x.group ('mark')), e)


                self.scr_mgr.qscr.clear ()

                self.scr_mgr.qscr.addstr (0, 0, y)

                self.msgyx = [0]
                self.msgyx.append ((self.scr_mgr.qscr.getyx ()[0] + 1) * self.scr_mgr.scrdim
                        [1])

                self.scr_mgr.qline = 0

                self.scr_mgr.qscr.noutrefresh (self.scr_mgr.qline, 0, self.scr_mgr.scord[0], self.scr_mgr.scord [1],
                        (self.scr_mgr.scrdim [0] + self.scr_mgr.scord [0]) - 1, (self.scr_mgr.scrdim [1] + self.scr_mgr.scord
                            [1]) - 1)


            else:
                self.qst = None
                return self.update_qscr ()

        else:
            qst = self.scr_mgr.qmgr.fetch (timeout = (30.5, 60))

            if not qst:
                return BREAK
        
            elif isinstance (qst, lxml.html.FieldsDict):

                x = copy.deepcopy (qst)

                x = self.amgr.answer (x)

                if x and x != self.amgr.NOANSWER and qst [self.scr_mgr.qmgr.qmap ['qid']] == x [self.scr_mgr.qmgr.qmap ['qid']]:
                    qst = x

                self.pq.append ((qst [self.scr_mgr.qmgr.qmap ['crscode']], qst
                    [self.scr_mgr.qmgr.qmap ['qid']]))

                self.pqlen += 1

                self.scr_mgr.pqidx = self.pqlen - 1
                self.scr_mgr.lpqidx = self.scr_mgr.pqidx

            self.qmode = True

            return self.update_qscr (qst)


    
    def update_qscr (self, qst = None, scr = None):

        if not scr:
            scr = self.scr_mgr

        optmap = []
        qline = 0

        if qst: 
            if scr is self.scr_mgr:
                self.qst = qst

            else:
                qline = scr.qline

            scr.qscr.move (0, 0)
            scr.qscr.clear ()

            for f in ['qdescr'] + ['opt' + chr (97 + i) for i in range (len (scr.qmgr.pseudos))]:
                if f.startswith ('opt'):
                    i = (ord (f[-1]) & 0x1f) - 1
                    x = scr.qscr.getyx ()
                    
                    if isinstance (scr.qmgr.pseudos [i], int):
                        scr.qscr.addch (scr.qmgr.pseudos [i])
                        pre = ''
                    else:
                        pre = scr.qmgr.pseudos [i] + ': '

                    scr.qscr.addstr (pre + qst [scr.qmgr.qmap [f]].strip ())
                    cur = scr.qscr.getyx ()
                    optmap.append ([
                        x[0],
                        (cur [0] - x[0]) * (scr.scrdim [1]) + cur [1],
                        scr.qmgr.pseudos [i] if isinstance (scr.qmgr.pseudos [i], int) else None,
                        curses.A_NORMAL
                        ])

                    scr.qscr.addch ('\n')

                elif f == 'qdescr':
                    if isinstance (qst [scr.qmgr.qmap ['qn']], int):
                        scr.qscr.addch (scr.qmgr.pseudos [i])
                        pre = ''
                    else:
                        pre = str (qst [scr.qmgr.qmap ['qn']]) + '. '

                    scr.qscr.addstr (pre + qst [scr.qmgr.qmap [f]].strip () + '\n')

                scr.qscr.addch ('\n')

            if not optmap:
                pass #NOTE: Draw a textbox for fill-in-the-gap answer
           

            elif qst [scr.qmgr.qmap ['qid']] != 'error':

                a = qst [scr.qmgr.qmap ['ans']]
                
                if a:
                    i = scr.qmgr.pseudos.index (a)

                    optmap [i][-1] = curses.A_BLINK

                else:
                    i = 0

            else:
                    i = 0

            self.paint (optmap [i])

        elif self.qst:
            pass

        else:
            qline = 0
            scr.qscr.clear ()
            scr.qscr.addstr (0, 0, 'Hit Enter to start')


        scr.qscr.noutrefresh (qline, 0, scr.scord[0], scr.scord [1],
                (scr.scrdim [0] + scr.scord [0]) - 1, (scr.scrdim [1] + scr.scord
                    [1]) - 1)

        if scr == self.scr_mgr:
            self.optmap = optmap
            self.scr_mgr.qline = qline

        return

    def ctrl_l18 (self):
        if self.qmode and self.qst:
            curses.flash ()
            self.update_qscr (self.qst)

    def paint (self, t = None, color = curses.A_BOLD | curses.A_REVERSE,
            undo = False, scr = None, optmap = None):

        scr = scr if scr else self.scr_mgr

        if t == None:
            optmap = optmap if optmap else self.optmap

            if not optmap:
                return

            cur = scr.qscr.getyx ()

            t = [x for x in optmap if x [0] == cur [0]]

            if not t:
                return

            else:
                t = t[0]

        c = divmod (t [1], scr.scrdim [1])
        l = t [0] 
        
        x = c[0]

        while x:
            scr.qscr.chgat (l, 0, (color) if not undo
                    else t[-1])
            l += 1
            x -= 1

        scr.qscr.chgat (l, 0, c [1], (color) if not undo
                else t [-1])
        
        if t [2]:
            scr.qscr.addch (t[0], 0, t[2])

        scr.qscr.move (t[0], 0)


def main (stdscr, args):

    class LoopMgr:
        def __init__ (self, matno, crscode, tma):

            self.scroll_status = True
            self.pad = curses.newpad (1, 10000)
            self.crsscr_dim = crsscr.getmaxyx ()
            self.cord = crsscr.getbegyx ()
            self.mkscrollscr (matno, crscode, tma)
            self.in_fut = False

            if self.scroll_status:
                self.sthread = threading.Thread (target = self.scroll, daemon = True)

                self.sthread.start ()

        def mkscrollscr (self, matno, crscode, tma):
            self.pad.clear ()

            self.pad.addstr (0, 0, matno + '  ' + crscode + ' TMA%s' % (tma,), curses.A_REVERSE)

            self.pwrite_len = self.pad.getyx ()[1]

        def stop_scroll (self):
            self.scroll_status = False
            return

        def scroll (self, t = 0.07):

            crsscr.clear ()
            crsscr.refresh ()
            self.right = crsscr.derwin (1, math.ceil (self.crsscr_dim [1] * (2/3)), 0, self.crsscr_dim [1] - math.ceil (self.crsscr_dim [1] * (2/3)))
            self.left = crsscr.derwin (1, math.floor (self.crsscr_dim [1] * (1/3)), 0, 0)

            self.rcord = self.right.getbegyx ()
            self.lcord = self.left.getbegyx ()

            self.rdim = self.right.getmaxyx ()
            self.ldim = self.left.getmaxyx ()
            self.rparam = [0, 0, self.rcord [0], self.rcord [1] + self.rdim [1] - 1, self.rcord [0], self.rcord [1] + self.rdim [1] - 1]

            self.lparam = [0, self.pwrite_len, self.lcord [0], self.lcord [1], self.lcord [0], self.lcord [1]]

            curses.curs_set (0)

            while self.scroll_status:
                self.pad.noutrefresh (*self.rparam)
                self.pad.noutrefresh (*self.lparam)
                time.sleep (t)

                curses.doupdate ()
                
                if self.rparam [3] > self.rcord [1]:
                    self.rparam [3] -= 1

                elif self.rparam [3] == self.rcord [1]:
                    if self.rparam [1] == self.pwrite_len:
                        self.rparam = [0, 0, self.rcord [0], self.rcord [1] + self.rdim [1] - 1, self.rcord [0], self.rcord [1] + self.rdim [1] - 1]

                    elif self.rparam [1] < self.pwrite_len:
                        self.rparam [1] += 1


                
                if self.rparam [3] > self.rcord [1]:
                    if self.lparam[3] > self.lcord [1]:
                        self.lparam [3] -= 1
                    elif self.lparam[3] == self.lcord [1]:
                        if self.lparam [1] <= (self.pwrite_len - 1):
                            self.lparam[1] += 1

                elif self.rparam [3] == self.rcord [1]:
                    if self.rparam [1] == 1:
                        self.lparam = [0, 0, self.lcord [0], self.lcord [1] + self.ldim [1] - 1, self.lcord [0],
                        self.lcord [1] + self.ldim [1] - 1]

                    elif self.rparam [1] > 1:
                        if self.lparam[3] > self.lcord [1]:
                            self.lparam [3] -= 1
                        elif self.lparam[3] == self.lcord [1]:
                            if self.lparam [1] <= (self.pwrite_len - 1):
                                self.lparam[1] += 1

                

        def __call__ (self, key):
            cmd = (getattr (self, k) for k in type (self).__dict__ if re.search
                (r'(?<!\d)' + str (key) + r'(?!\d)', k))
            try:
                return next (cmd)()
            except StopIteration:
                return

        def ctrl_l12 (self):
            stdscr.redrawwin ()
            update_scr ()

        def key_resize410 (self):
            
            nonlocal qstscr, inputscr, ipt_cord, crsscr

            curses.update_lines_cols()

            qstscr.resize (curses.LINES - 2, curses.COLS)
            inputscr.resize (1, curses.COLS)
            ipt_dim = inputscr.getmaxyx ()

            ipt_cord = inputscr.getbegyx ()
            crsscr.resize (1, curses.COLS)

            self.crsscr_dim = crsscr.getmaxyx ()
            self.cord = crsscr.getbegyx ()
            if self.scroll_status:
                self.scroll_status = False
                self.scroll_status = True

                self.sthread = threading.Thread (target = self.scroll, args = (0.70,), daemon = True)
                self.sthread.start ()
                
            qa_interface.resize_screen ()

        def ctrl_c3 (self):
            return BREAK

        def ctrl_x24 (self):
            pass

        def retro_114 (self):

            if not self.in_fut:
                ipt = []

                fields = ('Matric No', 'Password', 'Course code', 'Tma No', 'url')
                
                curses.echo ()
                curses.noraw ()

                for f in fields:
                    inputscr.clear ()
                    inputscr.addstr (0, 0, f + ': ', curses.A_BOLD)
                    inputscr.noutrefresh ()
                    update_scr ()
                    s = inputscr.getstr ()
                    s = s.decode ().strip () 
                    if re.match (r'quit', s, re.I):
                        curses.noecho ()
                        curses.raw ()
                        inputscr.clear ()
                        inputscr.noutrefresh ()
                        update_scr ()
                        return

                    ipt.append (s)

                curses.noecho ()
                curses.raw ()
                inputscr.clear ()
                inputscr.noutrefresh ()
                update_scr

                fut = threading.Thread (target = self.retrofit, kwargs = {'ipt':
                    ipt}, daemon = True)

                fut.start ()

                self.in_fut = True

            return


        def retrofit (self, ipt):

            url = ipt [4] or args.url

            if not url.startswith ('http'):
                url = 'https://' + url

            url += '/' if not url.endswith ('/') else ''

            matno = ipt [0] or args.matno
            crscode = ipt [2] or args.crscode

            tma = ipt [3] or args.tma

            pwd = ipt [1] or args.pwd

            farg = qstmgr.copy.deepcopy (fargs)

            farg ['url'] = re.sub (r'https?://.+/', url,
                    farg ['url'], flags = re.I)

            referer = re.sub (r'https?://.+/', url,
                    qstmgr.referer, flags = re.I)


            try:
                if url != args.url or not re.fullmatch (args.matno, matno , flags = re.I):


                    errpad.clear ()
                    errpad.addstr (0, 0, 'Sending first request to %s' % (url,))
                    errpad.noutrefresh (0, 0, ipt_cord [0], ipt_cord [1], ipt_cord [0] + ipt_dim [0] - 1, ipt_cord [1] + ipt_dim [1] - 1)
                    update_scr ()

                    nav.reconfigure (
                            url,
                            keys = {
                                mp ['kmap']['matno']: matno,
                                mp ['kmap']['pwd']: pwd 
                                },
                            )

                    errpad.clear ()
                    errpad.addstr (0, 0, 'Trying to logout %s' % (args.matno,))
                    errpad.noutrefresh (0, 0, ipt_cord [0], ipt_cord [1], ipt_cord [0] + ipt_dim [0] - 1, ipt_cord [1] + ipt_dim [1] - 1)
                    update_scr ()

                    nav ['logout_page']

                    errpad.clear ()
                    errpad.addstr (0, 0, 'Trying to login %s' % (matno,))
                    errpad.noutrefresh (0, 0, ipt_cord [0], ipt_cord [1], ipt_cord [0] + ipt_dim [0] - 1, ipt_cord [1] + ipt_dim [1] - 1)
                    update_scr ()

                    nav ['tma_page']

                else:

                    errpad.clear ()
                    errpad.addstr (0, 0, 'Skipping to login %s' % (matno,))
                    errpad.noutrefresh (0, 0, ipt_cord [0], ipt_cord [1], ipt_cord [0] + ipt_dim [0] - 1, ipt_cord [1] + ipt_dim [1] - 1)
                    update_scr ()

                qmgr = QstMgt.QstMgr (
                        fargs = farg,
                        url = referer,
                        qmap = qmap,
                        matno = matno,
                        crscode = crscode,
                        tma = tma,
                        session = nav.session
                        )

                qmgr.interactive = True

                inputscr.addstr (0, 0, 'done.')
                inputscr.noutrefresh ()
                update_scr ()

                qa_interface.qmgr = qmgr
                qa_interface.qtextscr.clear ()
                qa_interface.qst = None
                qa_interface.update_qscr ()
                args.matno = matno
                args.crscode = crscode
                args.tma = tma
                args.url = url
                args.pwd = pwd


                self.mkscrollscr (
                        args.matno,
                        args.crscode,
                        args.tma,

                        )
            
            except Exception as err:
                errpad.clear ()
                errpad.addstr (0, 0, 'Err: ' + repr (err))
                errpad.noutrefresh (0, 0, ipt_cord [0], ipt_cord [1], ipt_cord [0] + ipt_dim [0] - 1, ipt_cord [1] + ipt_dim [1] - 1)
                update_scr ()

            finally:
                self.in_fut = False



    def update_scr ():
        if not handler.scroll_status:
            curses.doupdate ()


    mp = configparser.ConfigParser (interpolation =
        configparser.ExtendedInterpolation ())

    mp.read (args.wmap)
    args.wmap = mp

    qmap = mp ['qmap']
    
    curses.start_color ()

    curses.noecho ()
   
    crsscr = stdscr.derwin (1, curses.COLS, 0, 0)
    

    qstscr = stdscr.derwin (curses.LINES - 2, curses.COLS, 1, 0)

    keys = MPCT_Preprocessor (**args.__dict__)

    scr_mgr = qscreen.QscrMuxer (qstscr, keys) 

    inputscr = stdscr.derwin (1, curses.COLS, curses.LINES - 1, 0)

    ipt_dim = inputscr.getmaxyx ()

    ipt_cord = inputscr.getbegyx ()

    #handler = LoopMgr (args.matno, args.crscode, args.tma)

    
    errpad = curses.newpad (10000, ipt_dim [1])

    ansmgr = AnsMgt.AnsMgr (
            qmap = qmap,
            database = args.database,
            mode = AnsMgt.AnsMgr.ANS_MODE_HACK | AnsMgt.AnsMgr.ANS_MODE_NORM,
            pseudo_ans = qmap ['pseudo_ans'].split (','),
            interactive = False,
            )

    qa_interface = Interface (
            scr_mgr,
            ansmgr
            ) 

    curses.doupdate ()

    while True:
        curses.raw ()
        qa_interface ['keypad'] (True)
        c = qa_interface ['getch'] ()
    
        c = qa_interface (c)
        curses.doupdate ()

        if c == BREAK:
            break


    if ansmgr._cur:
        f = open (args.qstdump, 'w')
        f.write ('[') 
        dbmgt.DbMgt.update_hacktab (args.database, ansmgr.iter_cache (), ansmgr.qmap,
                ansmgr._cur, f if args.debug else None)
        f.write (']')
        f.close ()

        ansmgr.close ()

    curses.noraw ()
    curses.echo ()
    curses.endwin ()

    return


if __name__ == '__main__':

    parser = argparse.ArgumentParser ()

    parser.add_argument ('--config', default = 'dogrc', help = 'configuration file to use', dest = 'wmap')

    parser.add_argument ('--debug', action = 'store_true', help = 'To enable debug mode')

    parser.add_argument ('--qstdump', default = 'dumpqst.json', help = 'The dump file for questions')

    parser.add_argument ('--database', '-db', default = 'pg/olddb', help = 'The database to use')


    parser.add_argument ('--url', help = 'The remote url if no local server',
            action = 'append', required = True)

    parser.add_argument ('--matno', help = 'Your Matric Number', default =
            ['Nou133606854'], action = 'append')

    parser.add_argument ('--pwd', help = 'Your pasword', default = ['12345'],
            action = 'append')

    parser.add_argument ('--crscode', help = 'Your target course', default =
            ['CIT701'], action = 'append')

    parser.add_argument ('--tma', help = 'Your target TMA for the chosen course', default = ['1'], action = 'append')


    args = parser.parse_args()
   

    try:
        
        stdscr = curses.initscr ()

        main (stdscr, args)

    except BaseException as err:
        curses.endwin ()
        raise err


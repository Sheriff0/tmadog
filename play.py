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

BREAK = 0

CONT = 1

TOP = 1

BOTTOM = 0

class ScrMgr:
    def __init__ (self, qscr, qmgr, amgr):
        self.qbdr = qscr
        self.qmgr = qmgr
        self.amgr = amgr
        cord, dim = self.qbdr.getbegyx (), self.qbdr.getmaxyx ()
        self.qcord, self.qdim = (cord [0] + 1, cord [1] + 1), (dim [0] - 2, dim [1] - 2) 

        self.qtextscr = curses.newpad (10000, self.qdim [1])

        
        self.qtextscr.keypad (True)

        curses.curs_set (0)
        
        self.qmgr.interactive = True

        self.qst = None
        self.qmode = True
        self.pq = []
        self.pqidx = -1
        self.pqlen = 0
        self.qbdr.box ()
        self.qbdr.noutrefresh ()
        self.update_qscr ()

    
    def __getitem__ (self, attr):
        return getattr (self.qtextscr, attr)

    def __call__ (self, key):
        cmd = (getattr (self, k) for k in type (self).__dict__ if re.search
                (r'(?<!\d)' + str (key) + r'(?!\d)', k))
        try:
            return next (cmd)()
        except StopIteration:
            raise NotImplementedError ('code %d not available' % (key,), key)

    def key_left260 (self):
        if self.qmode:
            if self.qst:
                if self.pqlen > (self.pqlen - self.pqidx) >= 1 and self.pqidx > 0:
                    self.pqidx -= 1
                
                    self.update_qscr (self.amgr.download (self.amgr (*self.pq
                        [self.pqidx]), self.amgr (*self.pq [-1]).copy ()))

    def key_right261 (self):
        if self.qmode:
            if self.qst:
                if self.pqlen >= (self.pqlen - self.pqidx) > 1:
                    self.pqidx += 1

                    self.update_qscr (self.amgr.download (self.amgr (*self.pq
                        [self.pqidx]), self.amgr (*self.pq [-1]).copy ()))


    def key_up259 (self):
        if self.qmode and self.optmap:
            cur = self.qtextscr.getyx ()
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
                        self.qline -= 1

                    else:
                        self.qline -= t[0]

                    self.qtextscr.move (t[0], 0)

                else:
                    self.qline -= 1

                self.paint ()

            except IndexError:
                if self.isseen ((0, self.qdim[1] - 1), TOP):
                    pass
                else:
                    self.qline -= 1

        elif not self.qmode:
            if not self.isseen (self.msgyx, TOP):
                self.qline -= 1


        self.qtextscr.noutrefresh (self.qline, 0, self.qcord[0], self.qcord [1],
        (self.qdim [0] + self.qcord [0]) - 1, (self.qdim [1] + self.qcord
            [1]) - 1)


    def key_down258 (self):
        if self.qmode and self.optmap:
            cur = self.qtextscr.getyx ()
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
                        self.qline += 1

                    else:
                        offset = t[0] - (self.qline + self.qdim[0] - 1)
                        self.qline += offset if offset >= 0 else 1

                    self.qtextscr.move (t[0], 0)

                elif self.isseen (self.optmap [n [0]], 1):
                    self.qline += 1

                else:
                    self.qline += 1


                self.paint ()

            except IndexError:
                if self.isseen (self.optmap [n [0]]):
                    pass
                else:
                    self.qline += 1


        elif not self.qmode:
            if not self.isseen (self.msgyx, BOTTOM):
                self.qline += 1

        self.qtextscr.noutrefresh (self.qline, 0, self.qcord[0], self.qcord [1],
        (self.qdim [0] + self.qcord [0]) - 1, (self.qdim [1] + self.qcord
            [1]) - 1)
                        


    def isseen (self, coord, dir = TOP):
        if dir == BOTTOM:
            x = math.floor (coord [1] / self.qdim [1]) + coord [0]
            y = (self.qline + self.qdim [0]) - 1
            return y >= x >= self.qline
        
        elif dir == TOP:
            x = coord [0]
            y = (self.qline + self.qdim [0]) - 1
            return self.qline <= x <= y


    def enter10 (self):

        if self.qmode:
            if self.qst: 
                c = chr (self ['inch'] () & 0xff)
                self.qst [self.qmgr.qmap ['ans']] = c
               
                e = self.qmgr.submit (self.qst)

                y = lxml.html.fromstring (self.qmgr.sres.text).text_content ()

                x = re.search (r'(?P<mark>[01])\s+mark for question', y, re.I)

                if x and self.qst [self.qmgr.qmap ['qid']] != 'error':
                    self.amgr.check (self.qst, int (x.group ('mark')), e)

                self.qmode = False

                self.qtextscr.clear ()

                self.qtextscr.addstr (0, 0, y)

                self.msgyx = [0]
                self.msgyx.append ((self.qtextscr.getyx ()[0] + 1) * self.qdim
                        [1])

                self.qline = 0

                self.qtextscr.noutrefresh (self.qline, 0, self.qcord[0], self.qcord [1],
                        (self.qdim [0] + self.qcord [0]) - 1, (self.qdim [1] + self.qcord
                            [1]) - 1)

            else:
                qst = self.qmgr.fetch (timeout = (30.5, 60))

                if not qst:
                    return BREAK
            
                elif isinstance (qst, lxml.html.FieldsDict):
                    x = qst

                    qst = x.copy ()

                    x = self.amgr.answer (x)

                    if x and qst [self.qmgr.qmap ['qid']] != x [self.qmgr.qmap ['qid']]:
                        try:
                            self.pq.index ((x [self.qmgr.qmap ['crscode']], x
                                [self.qmgr.qmap ['qid']]))
                        except ValueError:
                            self.pq.append ((x [self.qmgr.qmap ['crscode']], x
                                [self.qmgr.qmap ['qid']]))
                            self.pqlen += 1
                    else:
                        qst = x

                    self.pq.append ((qst [self.qmgr.qmap ['crscode']], qst
                        [self.qmgr.qmap ['qid']]))

                    self.pqlen += 1

                    self.pqidx = self.pqlen - 1

                return self.update_qscr (qst)

        else:
            qst = self.qmgr.fetch (timeout = (30.5, 60))

            if not qst:
                return BREAK
        
            elif isinstance (qst, lxml.html.FieldsDict):
                x = qst

                qst = x.copy ()

                x = self.amgr.answer (x)

                if qst [self.qmgr.qmap ['qid']] != x [self.qmgr.qmap ['qid']]:
                    try:
                        self.pq.index ((x [self.qmgr.qmap ['crscode']], x
                            [self.qmgr.qmap ['qid']]))
                    except ValueError:
                        self.pq.append ((x [self.qmgr.qmap ['crscode']], x
                            [self.qmgr.qmap ['qid']]))

                        self.pqlen += 1

                else:
                    qst = x

                self.pq.append ((qst [self.qmgr.qmap ['crscode']], qst
                    [self.qmgr.qmap ['qid']]))

                self.pqlen += 1

                self.pqidx = self.pqlen - 1

            self.qmode = True

            return self.update_qscr (qst)



    
    def update_qscr (self, qst = None):
        x = self.qtextscr.getyx ()

        if qst: 
            self.qst = qst

            self.optmap = []
            self.qline = 0
            self.qtextscr.move (0, 0)
            self.qtextscr.clear ()

            for f in ['qdescr'] + ['opt' + chr (97 + i) for i in range (len (self.qmgr.pseudos))]:
                if f.startswith ('opt'):
                    i = (ord (f[-1]) & 0x1f) - 1
                    x = self.qtextscr.getyx ()
                    
                    if isinstance (self.qmgr.pseudos [i], int):
                        self.qtextscr.addch (self.qmgr.pseudos [i])
                        pre = ''
                    else:
                        pre = self.qmgr.pseudos [i] + ': '

                    self.qtextscr.addstr (pre + self.qst [self.qmgr.qmap [f]].strip ())
                    cur = self.qtextscr.getyx ()
                    self.optmap.append ([
                        x[0],
                        (cur [0] - x[0]) * (self.qdim [1]) + cur [1],
                        self.qmgr.pseudos [i] if isinstance (self.qmgr.pseudos [i], int) else None,
                        curses.A_NORMAL
                        ])

                    self.qtextscr.addch ('\n')

                elif f == 'qdescr':
                    if isinstance (self.qst [self.qmgr.qmap ['qn']], int):
                        self.qtextscr.addch (self.qmgr.pseudos [i])
                        pre = ''
                    else:
                        pre = str (self.qst [self.qmgr.qmap ['qn']]) + '. '

                    self.qtextscr.addstr (pre + self.qst [self.qmgr.qmap [f]].strip () + '\n')

                self.qtextscr.addch ('\n')


            if not self.optmap:
                pass #NOTE: Draw a textbox for fill-in-the-gap answer
           

            elif qst [self.qmgr.qmap ['qid']] != 'error':

                a = qst [self.qmgr.qmap ['ans']]
                
                if a:
                    i = self.qmgr.pseudos.index (a)

                    self.optmap [i][-1] = curses.A_BLINK

                else:
                    i = 0

            else:
                    i = 0


            self.qtextscr.move (self.optmap [i][0], 0)

            self.paint ()

        elif self.qst:
            pass

        else:
            self.qline = 0
            self.qtextscr.addstr (0, 0, 'Hit Enter to start')


        self.qtextscr.noutrefresh (self.qline, 0, self.qcord[0], self.qcord [1],
                (self.qdim [0] + self.qcord [0]) - 1, (self.qdim [1] + self.qcord
                    [1]) - 1)

        return


    def paint (self, t = None, color = curses.A_BOLD | curses.A_REVERSE, undo = False):

        if not self.qst:
            return

        if t == None:
            cur = self.qtextscr.getyx ()
            t = [x for x in self.optmap if x [0] == cur [0]]

        if not t:
            return

        else:
            t = t[0]

            c = divmod (t [1], self.qdim [1])
            l = t [0] 
            
            x = c[0]

            while x:
                self.qtextscr.chgat (l, 0, (color) if not undo
                        else t[-1])
                l += 1
                x -= 1

            self.qtextscr.chgat (l, 0, c [1], (color) if not undo
                    else t [-1])
            
            if t [2]:
                self.qtextscr.addch (t[0], 0, t[2])

            self.qtextscr.move (t[0], 0)



def main (stdscr, args):

    class LoopMgr:
        def __init__ (self, matno, crscode, tma):
            self.scroll_status = True
            self.pad = curses.newpad (1, 10000)
            self.crsscr_dim = crsscr.getmaxyx ()
            self.cord = crsscr.getbegyx ()
            self.mkscrollscr (matno, crscode, tma)
            self.in_fut = False

        def mkscrollscr (self, matno, crscode, tma):
            self.pad.clear ()

            self.pad.addstr (0, 0, matno + '  ' + crscode + ' TMA%s' % (tma,), curses.A_REVERSE)

            self.pwrite_len = self.pad.getyx ()[1]

        def stop_scroll (self):
            self.scroll_status = False
            return

        def scroll (self, t = 0.07):

            right = crsscr.derwin (1, math.ceil (self.crsscr_dim [1] * (2/3)), 0, self.crsscr_dim [1] - math.ceil (self.crsscr_dim [1] * (2/3)))
            left = crsscr.derwin (1, math.floor (self.crsscr_dim [1] * (1/3)), 0, 0)

            rcord = right.getbegyx ()
            lcord = left.getbegyx ()

            rdim = right.getmaxyx ()
            ldim = left.getmaxyx ()
            
            rparam = [0, 0, rcord [0], rcord [1] + rdim [1] - 1, rcord [0],
                    rcord [1] + rdim [1] - 1]
            lparam = [0, self.pwrite_len, lcord [0], lcord [1], lcord [0], lcord [1]]

            curses.curs_set (0)

            while self.scroll_status:
                self.pad.noutrefresh (*rparam)
                self.pad.noutrefresh (*lparam)
                time.sleep (t)
                curses.doupdate ()
                
                if rparam [3] > rcord [1]:
                    rparam [3] -= 1

                elif rparam [3] == rcord [1]:
                    if rparam [1] == self.pwrite_len:
                        rparam = [0, 0, rcord [0], rcord [1] + rdim [1] - 1, rcord [0], rcord [1] + rdim [1] - 1]

                    elif rparam [1] < self.pwrite_len:
                        rparam [1] += 1


                
                if rparam [3] > rcord [1]:
                    if lparam[3] > lcord [1]:
                        lparam [3] -= 1
                    elif lparam[3] == lcord [1]:
                        if lparam [1] <= (self.pwrite_len - 1):
                            lparam[1] += 1

                elif rparam [3] == rcord [1]:
                    if rparam [1] == 1:
                        lparam = [0, 0, lcord [0], lcord [1] + ldim [1] - 1, lcord [0],
                        lcord [1] + ldim [1] - 1]

                    elif rparam [1] > 1:
                        if lparam[3] > lcord [1]:
                            lparam [3] -= 1
                        elif lparam[3] == lcord [1]:
                            if lparam [1] <= (self.pwrite_len - 1):
                                lparam[1] += 1

                

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

            nonlocal qstmgr, nav, mp

            url = ipt [4] or args.url

            if not url.startswith ('http'):
                url = 'https://' + url

            url += '/' if not url.endswith ('/') else ''

            matno = ipt [0] or args.matno
            crscode = ipt [2] or args.crscode

            tma = ipt [3] or args.tma

            pwd = ipt [1] or args.pwd

            farg = qstmgr.fargs.copy ()

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

                qa_scrmgr.qmgr = qmgr
                qa_scrmgr.qtextscr.clear ()
                qa_scrmgr.qst = None
                qa_scrmgr.update_qscr ()
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


    mp = configparser.ConfigParser (interpolation =
        configparser.ExtendedInterpolation ())

    mp.read (args.config)

    qmap = mp ['qmap']
    
    pseudos = qmap ['pseudo_ans'].split (',')


    session = cfscrape.create_scraper ()

    nav = Navigation.Navigator (
            args.url,
            mp, 
            {
                '[Matric Number]': args.matno,
                '[Password]': args.pwd 
                },
            session = session
            )
            
    #nav ['profile_page']
    t = nav ('qst_page')[:-1]

    qstmgr = QstMgt.QstMgr (
            matno = args.matno,
            crscode = args.crscode,
            tma = args.tma,
            fargs = t [0],
            stop = 10,
            url = t [1].url,
            qmap = qmap,
            session = session

            )

    def update_scr ():
        if not handler.scroll_status:
            curses.doupdate ()

    curses.start_color ()

    curses.noecho ()
   
    crsscr = stdscr.derwin (1, curses.COLS, 0, 0)
    

    qstscr = stdscr.derwin (curses.LINES - 2, curses.COLS, 1, 0)


    inputscr = stdscr.derwin (1, curses.COLS, curses.LINES - 1, 0)

    ipt_dim = inputscr.getmaxyx ()

    ipt_cord = inputscr.getbegyx ()

    handler = LoopMgr (args.matno, args.crscode, args.tma)

    sthread = threading.Thread (target = handler.scroll, daemon = True)

    sthread.start ()
    
    errpad = curses.newpad (10000, ipt_dim [1])

    ansmgr = AnsMgt.AnsMgr (
            qmap = qmap,
            database = args.database,
            mode = AnsMgt.AnsMgr.ANS_MODE_HACK | AnsMgt.AnsMgr.ANS_MODE_NORM,
            pseudo_ans = qmap ['pseudo_ans'].split (','),
            interactive = False,
            )

    qa_scrmgr = ScrMgr (
            qscr = qstscr,
            qmgr = qstmgr,
            amgr = ansmgr
            ) 

    while True:
        curses.raw ()
        c = qa_scrmgr ['getch'] ()
        
        try:
            c = qa_scrmgr (c)
            update_scr ()
        except NotImplementedError:
            try:
                c = handler (c)
                update_scr ()
            except Exception as err:
                curses.raw () 
                curses.nl ()
                curses.curs_set (0)
                errpad.keypad (True)
                inputscr.keypad (True)
                errpad.clear ()
                errpad.addstr (0, 0, err.args [0])
                cur = errpad.getyx ()

                line = 0

                while True:
                    errpad.noutrefresh (line, 0, ipt_cord [0], ipt_cord [1], ipt_cord [0] + ipt_dim [0] - 1, ipt_cord [1] + ipt_dim [1] - 1)
                    
                    update_scr ()
                    c = inputscr.getch ()
                    if c == curses.KEY_RIGHT or c == curses.KEY_DOWN:
                        if (line + ipt_dim [0] - 1) < cur [0]:
                            line += 1

                    elif c == curses.KEY_UP or c == curses.KEY_LEFT:
                        if line > 0:
                            line -= 1
                    elif c == curses.ascii.NL:
                        inputscr.clear ()
                        inputscr.noutrefresh ()
                        update_scr ()
                        break


        if c == BREAK:
            break


    if ansmgr._cur:
        f = open (args.qstdump, 'w')
        f.write ('[') 
        dbmgt.DbMgt.update_hacktab (args.database, ansmgr.iter_cache (), ansmgr.qmap,
                ansmgr._cur, f if args.debug else None)
        f.seek (-1, 1) 
        f.write (']')
        f.close ()

        ansmgr.close ()

    curses.noraw ()
    curses.echo ()
    handler.stop_scroll ()
    curses.endwin ()

    return


if __name__ == '__main__':

    parser = argparse.ArgumentParser ()

    parser.add_argument ('--config', default = 'dogrc', help = 'configuration file to use')

    parser.add_argument ('--debug', action = 'store_true', help = 'To enable debug mode')

    parser.add_argument ('--qstdump', default = 'dumpqst.json', help = 'The dump file for questions')

    parser.add_argument ('--database', '-db', default = 'pg/olddb', help = 'The database to use')


    parser.add_argument ('--url', help = 'The remote url if no local server', required = True)

    parser.add_argument ('--matno', help = 'Your Matric Number', default = 'Nou133606854')

    parser.add_argument ('--pwd', help = 'Your pasword', default = '12345')

    parser.add_argument ('--crscode', help = 'Your target course', default = 'CIT701')

    parser.add_argument ('--tma', help = 'Your target TMA for the chosen course', default = '1')


    args = parser.parse_args()
   

    try:
        
        stdscr = curses.initscr ()

        main (stdscr, args)

    except BaseException as err:
        curses.endwin ()
        raise err


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
import curses
import curses.ascii
import cfscrape
import concurrent.futures


BREAK = 0

CONT = 1

class ScrMgr:
    def __init__ (self, qscr, ascr, qmgr):
        self.qbdr = qscr
        self.qmgr = qmgr
        self.abdr = ascr
        cord, dim = self.qbdr.getbegyx (), self.qbdr.getmaxyx ()
        self.qcord, self.qdim = (cord [0] + 1, cord [1] + 1), (dim [0] - 2, dim [1] - 2) 

        cord, dim = self.abdr.getbegyx (), self.abdr.getmaxyx ()
        self.acord, self.adim = (cord [0] + 1, cord [1] + 1), (dim [0] - 2, dim [1] - 2) 

        self.qtextscr = curses.newpad (10000, self.qdim [1])

        self.atextscr = curses.newpad (10000, self.adim [1])
        
        self.atextscr.keypad (True)
        self.qtextscr.keypad (True)

        self.qbdr.attrset (curses.A_NORMAL)
        self.abdr.attrset (curses.A_NORMAL)
        curses.curs_set (0)
        
        self.qmgr.interactive = True

        self.is_qscr = True
        self.qst = None
        self.pq = []
        self.pqidx = 0
        self.qbdr.box ()
        self.qbdr.noutrefresh ()
        self.abdr.box (' ', ' ')
        self.abdr.noutrefresh ()
        self.update_qscr ()
        self.update_ascr ()

    
    def __getitem__ (self, attr):
        return getattr (self.qtextscr if self.is_qscr else self.atextscr, attr)

    def __call__ (self, key):
        cmd = (getattr (self, k) for k in type (self).__dict__ if re.search
                (r'(?<!\d)' + str (key) + r'(?!\d)', k))
        try:
            return next (cmd)()
        except StopIteration:
            raise NotImplementedError ('code %d not available' % (key,), key)

    def key_up259 (self):
        if self.is_qscr and self.optmap:
            cur = self.qtextscr.getyx ()
            n = [i for i,t in enumerate (self.optmap) if t[0] == cur [0]]

            if not n:
                return

            try:
                t = n [0] - 1
                
                if t < 0:
                    raise IndexError (t)
                t = self.optmap [t]

                if self.isseen (self.optmap [n [0]], 1):
                    self.paint (undo = True)


                    if self.isseen (t, 1):
                        pass

                    elif self.isseen (t, 0):
                        self.qline -= 1

                    else:
                        self.qline -= t[0]

                    self.qtextscr.move (t[0], 0)

                else:
                    self.qline -= 1

                self.paint ()

            except IndexError:
                if self.isseen ((0, self.qdim[1] - 1), 1):
                    pass
                else:
                    self.qline -= 1


            finally:
                qst = self.qst
                self.qst = None
                self.update_qscr () 
                self.qst = qst


    def key_down258 (self):
        if self.is_qscr and self.optmap:
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

            finally:
                self.qtextscr.noutrefresh (self.qline, 0, self.qcord[0], self.qcord [1],
                (self.qdim [0] + self.qcord [0]) - 1, (self.qdim [1] + self.qcord
                    [1]) - 1)
                        


    def isseen (self, coord, dir = 0):
        if not dir:
            x = math.floor (coord [1] / self.qdim [1]) + coord [0]
            y = (self.qline + self.qdim [0]) - 1
            return y >= x >= self.qline
        
        else:
            x = coord [0]
            y = (self.qline + self.qdim [0]) - 1
            return self.qline <= x <= y

    def ctrl_w23 (self):
        c = self ['getch'] ()

        if c == curses.KEY_RIGHT or c == curses.KEY_LEFT:
            if self.is_qscr:
                self.qbdr.box (' ', ' ')
                self.qbdr.noutrefresh ()
                self.abdr.box ()
                self.abdr.noutrefresh ()
            else:
                self.qbdr.box ()
                self.qbdr.noutrefresh ()
                self.abdr.box (' ', ' ')
                self.abdr.noutrefresh ()

            self.is_qscr = not self.is_qscr
            qst = self.qst
            self.qst = None
            self.update_qscr ()
            self.update_ascr ()
            self.qst = qst

        else:
            return

    def enter10 (self):
        if self.is_qscr:
            if self.qst: 
                c = chr (self ['inch'] () & 0xff)
                self.qst [self.qmgr.qmap ['ans']] = c
               
                x = self.qmgr.submit (self.qst)

                if x != None:
                    self.pq.append ((self.qst, x))


            self.qst = self.qmgr.fetch (timeout = (30.5, 60))
            if not self.qst:
                return BREAK

            return self.update_qscr ()
        else:
            return

    
    def update_qscr (self, qst = None):

        self.qst = qst if qst else self.qst
        x = self.qtextscr.getyx ()

        if self.qst: 

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
                    self.optmap.append ((
                        x[0],
                        (cur [0] - x[0]) * (self.qdim [1]) + cur [1],
                        self.qmgr.pseudos [i] if isinstance (self.qmgr.pseudos [i], int) else None
                        ))
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

            self.qtextscr.move (self.optmap [0][0], 0)

            self.paint ()

        elif x[0] >= 1:
            pass

        else:
            self.qline = 0
            self.qtextscr.addstr (0, 0, 'Hit Enter to start')


        self.qtextscr.noutrefresh (self.qline, 0, self.qcord[0], self.qcord [1],
                (self.qdim [0] + self.qcord [0]) - 1, (self.qdim [1] + self.qcord
                    [1]) - 1)


        return

    def update_ascr (self):
        pass

    def paint (self, undo = False):

        if self.is_qscr:
            if not self.qst:
                return
            cur = self.qtextscr.getyx ()
            t = [x for x in self.optmap if x [0] == cur [0]]

            if not t:
                return

            else:
                c = divmod (t [0][1], self.qdim [1])
                l = t [0][0] 
                
                x = c[0]

                while x:
                    self.qtextscr.chgat (l, 0, (curses.A_BOLD |
                        curses.A_REVERSE) if not undo
                            else curses.A_NORMAL)
                    l += 1
                    x -= 1

                self.qtextscr.chgat (l, 0, c [1], (curses.A_BOLD |
                    curses.A_REVERSE) if not undo
                        else curses.A_NORMAL)
                
                if t [0][2]:
                    self.qtextscr.addch (t[0][0], 0, t[0][2])

                self.qtextscr.move (t[0][0], 0)



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

            nonlocal qstmgr, nav

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


            session = None

            
            try:
                if url != args.url or not re.fullmatch (args.matno, matno , flags = re.I):

                    session = cfscrape.create_scraper ()

                    errpad.clear ()
                    errpad.addstr (0, 0, 'Sending first request to %s' % (url,))
                    errpad.noutrefresh (0, 0, ipt_cord [0], ipt_cord [1], ipt_cord [0] + ipt_dim [0] - 1, ipt_cord [1] + ipt_dim [1] - 1)
                    update_scr ()

                    nav = Navigation.Navigator (
                            url,
                            mp, 
                            {
                                '[Matric Number]': matno,
                                '[Password]': pwd 
                                },
                            session = session,
                            timeout = (30.5, 60)
                            )

                    errpad.clear ()
                    errpad.addstr (0, 0, 'Trying to login %s' % (matno,))
                    errpad.noutrefresh (0, 0, ipt_cord [0], ipt_cord [1], ipt_cord [0] + ipt_dim [0] - 1, ipt_cord [1] + ipt_dim [1] - 1)
                    update_scr ()

                    nav ['profile_page']

                else:

                    session = nav.session

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
                        session = session
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
            
    t = nav ('tma_page')[:-1]

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
    

    qstscr = stdscr.derwin (curses.LINES - 2, math.trunc (curses.COLS * (3/4)), 1, 0)

    resscr = stdscr.derwin (curses.LINES - 2, math.trunc (curses.COLS * (1/4)), 1,
            curses.COLS - math.trunc (curses.COLS * (1/4)))

    inputscr = stdscr.derwin (1, curses.COLS, curses.LINES - 1, 0)

    ipt_dim = inputscr.getmaxyx ()

    ipt_cord = inputscr.getbegyx ()

    handler = LoopMgr (args.matno, args.crscode, args.tma)

    sthread = threading.Thread (target = handler.scroll, daemon = True)

    sthread.start ()
    
    errpad = curses.newpad (10000, ipt_dim [1])

    qa_scrmgr = ScrMgr (
            qscr = qstscr,
            ascr = resscr,
            qmgr = qstmgr,
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


    curses.noraw ()
    curses.echo ()
    handler.stop_scroll ()
    return

if __name__ == '__main__':

    parser = argparse.ArgumentParser ()

    parser.add_argument ('--config', default = 'dogrc', help = 'configuration file to use')


    parser.add_argument ('--url', help = 'The remote url if no local server', required = True)

    parser.add_argument ('--matno', help = 'Your Matric Number', default = 'Nou133606854')

    parser.add_argument ('--pwd', help = 'Your pasword', default = '12345')

    parser.add_argument ('--crscode', help = 'Your target course', default = 'CIT701')

    parser.add_argument ('--tma', help = 'Your target TMA for the chosen course', default = '1')


    args = parser.parse_args()
   

    try:
        
        stdscr = curses.initscr ()

        main (stdscr, args)
        curses.endwin ()

    except BaseException as err:
        curses.endwin ()
        raise err


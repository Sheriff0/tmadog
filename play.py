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

        self.is_qscr = False
        self.qst = None
        self.pq = []
        self.pqidx = 0
        self.update_qscr ()
        self.update_ascr ()

    
    def __getitem__ (self, attr):
        return getattr (self.qtextscr if self.is_qscr else self.atextscr, attr)

    def __call__ (self, key):
        cmd = (getattr (self, k) for k in type (self).__dict__ if k.endswith (str (key)))
        try:
            next (cmd)()
        except StopIteration:
            raise NotImplementedError ('code %d not available' % (key,), key)

    def ctrl_c3 (self):
        return BREAK

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
                self.qtextscr.refresh (self.qline, 0, self.qcord[0], self.qcord [1],
                (self.qdim [0] + self.qcord [0]) - 1, (self.qdim [1] + self.qcord
                    [1]) - 1)
                        


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
                    t = self.optmap [n [0]]
                    offset = t[0] - (self.qline + self.qdim[0] - 1)
                    self.qline += offset if offset >= 0 else 0


                self.paint ()

            except IndexError:
                if self.isseen (self.optmap [n [0]]):
                    pass
                else:
                    self.qline += 1

            finally:
                self.qtextscr.refresh (self.qline, 0, self.qcord[0], self.qcord [1],
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
            self ['box'] (' ', ' ')
            self ['noutrefresh'] ()
            self.is_qscr = not self.is_qscr
            if not self.is_qscr:
                curses.curs_set (0)
            else:
                curses.curs_set (1)

            self ['box'] ()
            self ['noutrefresh'] ()
            curses.doupdate ()

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


            self.qst = self.qmgr.fetch ()

            return self.update_qscr ()
        else:
            return

    
    def update_qscr (self, qst = None):

        self.optmap = []
        self.qline = 0
        self.qtextscr.move (0, 0)
        self.qtextscr.clear ()

        if self.qst: 
            self.qst = qst if qst else self.qst


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

        else:
            self.qtextscr.addstr (0, 0, 'Hit Enter to start')

        self.qbdr.box ()
        self.is_qscr = True
        self.paint ()
        self.qbdr.noutrefresh ()

        self.qtextscr.noutrefresh (self.qline, 0, self.qcord[0], self.qcord [1],
                (self.qdim [0] + self.qcord [0]) - 1, (self.qdim [1] + self.qcord
                    [1]) - 1)

        curses.doupdate ()

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


    def mkprompt (qmap, pseudos):
        txt = '''{%s}. {%s}

''' % (qmap ['qn'], qmap ['qdescr'])

        for i in range (len (pseudos)):
            k = 'opt' + chr (65+i)
            txt += '%s: {%s}\n' % (pseudos [i], qmap [k])

        return txt

    

    mp = configparser.ConfigParser (interpolation =
        configparser.ExtendedInterpolation ())

    mp.read (args.config)

    qmap = mp ['qmap']
    
    pseudos = qmap ['pseudo_ans'].split (',')

    ptext = mkprompt (qmap, pseudos)

    session = requests.Session ()

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

    curses.start_color ()

    curses.noecho ()
   
    crsscr = stdscr.derwin (1, curses.COLS, 0, 0)
    
    crsscr.addstr (0, math.trunc (curses.COLS/2) - math.trunc (len
        (args.crscode) / 2), args.crscode, curses.A_REVERSE)

    crsscr.refresh ()

    qstscr = stdscr.derwin (curses.LINES - 1, math.trunc (curses.COLS * (3/4)), 1, 0)

    resscr = stdscr.derwin (curses.LINES - 1, math.trunc (curses.COLS * (1/4)), 1,
            curses.COLS - math.trunc (curses.COLS * (1/4)))
    

    qa_scrmgr = ScrMgr (
            qscr = qstscr,
            ascr = resscr,
            qmgr = qstmgr,
            ) 

    while True:
        curses.raw ()
        c = qa_scrmgr ['getch'] ()

        c = qa_scrmgr (c)

        if c == BREAK:
            return



if __name__ == '__main__':

    parser = argparse.ArgumentParser ()

    parser.add_argument ('--config', default = 'myrc', help = 'configuration file to use')


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


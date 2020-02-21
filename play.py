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
    def __init__ (self, qscr, ascr, qmgr, qmap, pseudos):
        self.qbdr = qscr
        self.qmgr = qmgr
        self.abdr = ascr
        self.qmap = qmap
        self.pseudos = pseudos
        cord, dim = self.qbdr.getbegyx (), self.qbdr.getmaxyx ()
        self.qcord, self.qdim = (cord [0] + 1, cord [1] + 1), (dim [0] - 2, dim [1] - 2) 

        cord, dim = self.abdr.getbegyx (), self.abdr.getmaxyx ()
        self.acord, self.adim = (cord [0] + 1, cord [1] + 1), (dim [0] - 2, dim [1] - 2) 

        self.qtextscr = curses.newpad (10000, self.qdim [1])

        self.atextscr = curses.newpad (10000, self.adim [1])
        
        self.atextscr.keypad (True)
        self.qtextscr.keypad (True)

        self.qbdr.attrset (curses.A_REVERSE)
        self.abdr.attrset (curses.A_REVERSE)

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
        pass

    def key_down258 (self):
        if self.is_qscr and self.optmap:
            cur = self.qtextscr.getyx ()
            n = [i for i,t in enumerate (self.optmap) if t[0] == cur [0]]

            if not n:
                return

            try:
                if self.isseen (self.optmap [n [0]]):
                    self.paint (True)

                    t = self.optmap [n [0]+ 1]
                    if self.isseen (t):
                        pass
                    else:
                        offset = math.ceil (t [1]/self.qdim [1]) 
                        self.qline += offset

                    self.qtextscr.move (t[0], 0)
                    self.paint ()

            except IndexError:
                pass


    def isseen (self, coord):
        x = math.floor (coord [1] / self.qdim [1]) + coord [0]
        y = (self.qline + self.qdim [0])
        return y >= x

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
                self.qst [self.qmap ['ans']] = c
                
                self.pq.append ((self.qst, self.qmgr.submit (self.qst)))


            self.qst = self.qmgr.fetch ()
            return self.update_qscr ()
        else:
            return

    
    def update_qscr (self, qst = None):

        self.optmap = self.pseudos.copy ()
        self.qline = 0
        self.qtextscr.move (0, 0)
        self.qtextscr.clear ()

        if self.qst: 
            self.qst = qst if qst else self.qst


            for f in ['qdescr'] + ['opt' + chr (97 + i) for i in range (len (self.pseudos))]:
                if f.startswith ('opt'):
                    i = (ord (f[-1]) & 0x1f) - 1
                    cur = self.qtextscr.getyx ()
                    self.optmap [i] = cur
                    pre = self.pseudos [i] + ': '
                    self.qtextscr.addstr (pre + self.qst [self.qmap [f]])
                    cur = self.qtextscr.getyx ()
                    self.optmap [i] = (self.optmap [i][0], (cur [0] - self.optmap [i][0]) * (self.qdim [1]) + cur [1])

                elif f == 'qdescr':
                    pre = str (self.qst [self.qmap ['qn']]) + '. '

                    self.qtextscr.addstr (pre + self.qst [self.qmap [f]] + '\n')

                self.qtextscr.addch ('\n')
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
                    self.qtextscr.chgat (l, 0, curses.A_UNDERLINE if not undo
                            else curses.A_NORMAL)
                    l += 1
                    x -= 1

                self.qtextscr.chgat (l, 0, c [1], curses.A_UNDERLINE if not undo
                        else curses.A_NORMAL)

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

    qstscr = stdscr.derwin (curses.LINES - 1, math.trunc (curses.COLS/2), 1, 0)

    resscr = stdscr.derwin (curses.LINES - 1, math.trunc (curses.COLS/2), 1,
            math.trunc (curses.COLS/2))
    

    qa_scrmgr = ScrMgr (
            qscr = qstscr,
            ascr = resscr,
            qmgr = qstmgr,
            qmap = qmap,
            pseudos = pseudos
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


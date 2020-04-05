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
import cloudscraper
import concurrent.futures
import lxml
import qscreen
import copy
import pdb

BREAK = -1

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
        self.len = max (len (self.crscodes), len (self.tmas))

    def __len__ (self):
        return self.len

    def __iter__ (self):
        yield from self.__next__ ()

    def __next__ (self):

        for i in range (self.len):

            try:
                self.param [self.MATNO] = self.matnos [i]
                self.param [self.PWD] = self.pwds [i]
                self.param [self.CRSCODE] = self.crscodes [i]
                self.param [self.TMA] = self.tmas [i]
                self.param [self.URL] = self.urls [i]
            
            except IndexError:
                try:
                    self.param [self.CRSCODE] = self.crscodes [i]
                    self.param [self.TMA] = self.tmas [i]
                    self.param [self.URL] = self.urls [i]
                
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
        self.scr_mgr ['qst'] = None
        self.qmode = True
        self.pq = []
        self.pqlen = 0
        self.stdscr = stdscr
        self.update_qscr ()

    def __getitem__ (self, attr):
        return getattr (self.scr_mgr ['qscr'], attr)

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

            elif c <= 255:
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


    def key_left260 (self, subtrahend = 1):
        if self.qmode:
            
            if isinstance (subtrahend, bytearray):
                if not subtrahend.isdigit ():
                    return
                subtrahend = int (subtrahend.decode())

            if self.pq:
                l = self.amgr (*self.pq [self.scr_mgr ['lpqidx']])

                self.scr_mgr ['pqidx'] -= subtrahend
                
                if 0 <= self.scr_mgr ['pqidx'] < self.pqlen:
                        p = self.amgr (*self.pq [self.scr_mgr ['pqidx']])

                        if p and l:
                            self.update_qscr (self.amgr.download (p, l))

                elif self.scr_mgr ['pqidx'] < 0:
                    self.scr_mgr ['pqidx'] = 0


    def key_right261 (self, addend = 1):
        if self.qmode and self.pq:
            l = self.amgr (*self.pq [self.scr_mgr ['lpqidx']])

            if isinstance (addend, bytearray):
                if not addend.isdigit ():
                    return
                addend = int (addend.decode())

            self.scr_mgr ['pqidx'] += addend
            
            if 0 <= self.scr_mgr ['pqidx'] < self.pqlen:
                p = self.amgr (*self.pq [self.scr_mgr ['pqidx']])

                if p and l:
                    self.update_qscr (self.amgr.download (p, l))

            elif self.scr_mgr ['pqidx'] >= self.pqlen:
                if (self.scr_mgr ['pqidx'] - self.scr_mgr ['lpqidx']) == 1:
                    self.scr_mgr ['pqidx'] = self.pqlen - 1
                    return 

                self.scr_mgr ['pqidx'] = self.pqlen - 1

                if l:
                    self.update_qscr (l)


    def key_up259 (self, subtrahend = 1):
        if isinstance (subtrahend, bytearray):
            if not subtrahend.isdigit ():
                return

            subtrahend = int (subtrahend.decode())

        if self.qmode and self.scr_mgr ['optmap']:
            cur = self.scr_mgr ['qscr'].getyx ()
            n = [i for i,t in enumerate (self.scr_mgr ['optmap']) if t[0] == cur [0]]

            if not n:
                return

            try:
                t = n [0] - 1
                
                if t < 0:
                    raise IndexError (t)
                t = self.scr_mgr ['optmap'] [t]

                if self.isseen (self.scr_mgr ['optmap'] [n [0]], TOP):
                    self.paint (undo = True)


                    if self.isseen (t, TOP):
                        pass

                    elif self.isseen (t, BOTTOM):
                        self.scr_mgr ['qline'] -= subtrahend

                    else:
                        self.scr_mgr ['qline'] -= t[0]

                    self.scr_mgr ['qscr'].move (t[0], 0)

                elif self.scr_mgr ['qline'] > 0:
                    self.scr_mgr ['qline'] -= subtrahend

                self.paint ()

                n [0] -= subtrahend

            except IndexError:
                if self.scr_mgr ['qline'] == 0:
                    pass
                else:
                    self.scr_mgr ['qline'] -= subtrahend

            self.scr_mgr ['qscr'].noutrefresh (self.scr_mgr ['qline'], 0, self.scr_mgr.scord[0], self.scr_mgr.scord [1],
            (self.scr_mgr.scrdim [0] + self.scr_mgr.scord [0]) - 1, (self.scr_mgr.scrdim [1] + self.scr_mgr.scord
                [1]) - 1)

            return n [0]

        elif not self.qmode:
            if not self.isseen (self.msgyx, TOP):
                self.scr_mgr ['qline'] -= subtrahend


            self.scr_mgr ['qscr'].noutrefresh (self.scr_mgr ['qline'], 0, self.scr_mgr.scord[0], self.scr_mgr.scord [1],
            (self.scr_mgr.scrdim [0] + self.scr_mgr.scord [0]) - 1, (self.scr_mgr.scrdim [1] + self.scr_mgr.scord
                [1]) - 1)


    def key_down258 (self, addend = 1):
        if isinstance (addend, bytearray):
            if not addend.isdigit ():
                return

            addend = int (addend.decode())

        if self.qmode and self.scr_mgr ['optmap']:
            cur = self.scr_mgr ['qscr'].getyx ()
            n = [i for i,t in enumerate (self.scr_mgr ['optmap']) if t[0] == cur [0]]

            if not n:
                return

            try:
                t = self.scr_mgr ['optmap'] [n [0] + 1]

                if self.isseen (self.scr_mgr ['optmap'] [n [0]]):
                    self.paint (undo = True)


                    if self.isseen (t, 0):
                        pass

                    elif self.isseen (t, 1):
                        self.scr_mgr ['qline'] += addend

                    else:
                        offset = t[0] - (self.scr_mgr ['qline'] + self.scr_mgr.scrdim[0] - 1)
                        self.scr_mgr ['qline'] += offset if offset >= 0 else 1

                    self.scr_mgr ['qscr'].move (t[0], 0)

                elif self.isseen (self.scr_mgr ['optmap'] [n [0]], 1):
                    self.scr_mgr ['qline'] += addend

                else:
                    self.scr_mgr ['qline'] += addend


                self.paint ()

                n [0] += addend

            except IndexError:
                if self.isseen (self.scr_mgr ['optmap'] [n [0]]):
                    pass
                else:
                    self.scr_mgr ['qline'] += addend


            self.scr_mgr ['qscr'].noutrefresh (self.scr_mgr ['qline'], 0, self.scr_mgr.scord[0], self.scr_mgr.scord [1],
            (self.scr_mgr.scrdim [0] + self.scr_mgr.scord [0]) - 1, (self.scr_mgr.scrdim [1] + self.scr_mgr.scord
                [1]) - 1)
                          
            return n [0]

        elif not self.qmode:
            if not self.isseen (self.msgyx, BOTTOM):
                self.scr_mgr ['qline'] += addend

            self.scr_mgr ['qscr'].noutrefresh (self.scr_mgr ['qline'], 0, self.scr_mgr.scord[0], self.scr_mgr.scord [1],
            (self.scr_mgr.scrdim [0] + self.scr_mgr.scord [0]) - 1, (self.scr_mgr.scrdim [1] + self.scr_mgr.scord
                [1]) - 1)
                            

    def isseen (self, coord, dir = TOP):
        if dir == BOTTOM:
            x = math.floor (coord [1] / self.scr_mgr.scrdim [1]) + coord [0]
            y = (self.scr_mgr ['qline'] + self.scr_mgr.scrdim [0]) - 1
            return y >= x >= self.scr_mgr ['qline']
        
        elif dir == TOP:
            x = coord [0]
            y = (self.scr_mgr ['qline'] + self.scr_mgr.scrdim [0]) - 1
            return self.scr_mgr ['qline'] <= x <= y


    def enter10 (self, c = False):

        if self.qmode and self.scr_mgr ['qst']: 
            if c == False:
                c = self ['instr'] (len (self.scr_mgr ['qmgr'].pseudos [0]))

            c = c.decode ()

            self.scr_mgr ['qst'] [self.scr_mgr ['qmgr'].qmap ['ans']] = c
           
            e = self.scr_mgr ['qmgr'].submit (self.scr_mgr ['qst'])


            if self.scr_mgr ['qst'] [self.scr_mgr ['qmgr'].qmap ['qid']] != 'error' and hasattr (self.scr_mgr ['qmgr'], 'sres'):
                self.qmode = False

                y = lxml.html.fromstring (self.scr_mgr ['qmgr'].sres.text).text_content ()

                x = re.search (r'(?P<mark>[01])\s+mark for question', y, re.I)

                if x:
                    self.amgr.check (self.scr_mgr ['qst'], int (x.group ('mark')), e)


                self.scr_mgr ['qscr'].clear ()

                self.scr_mgr ['qscr'].addstr (0, 0, y)

                self.msgyx = [0]
                self.msgyx.append ((self.scr_mgr ['qscr'].getyx ()[0] + 1) * self.scr_mgr.scrdim
                        [1])

                self.scr_mgr ['qline'] = 0

                self.scr_mgr ['qscr'].noutrefresh (self.scr_mgr ['qline'], 0, self.scr_mgr.scord[0], self.scr_mgr.scord [1],
                        (self.scr_mgr.scrdim [0] + self.scr_mgr.scord [0]) - 1, (self.scr_mgr.scrdim [1] + self.scr_mgr.scord
                            [1]) - 1)


            else:
                self.scr_mgr ['qst'] = None
                return self.update_qscr ()

        else:
            qst = self.scr_mgr ['qmgr'].fetch (timeout = (30.5, 60))

            if not qst:
                return BREAK
        
            elif isinstance (qst, lxml.html.FieldsDict):

                x = copy.deepcopy (qst)

                x = self.amgr.answer (x)

                if x and x != self.amgr.NOANSWER and qst [self.scr_mgr ['qmgr'].qmap ['qid']] == x [self.scr_mgr ['qmgr'].qmap ['qid']]:
                    qst = x

                self.pq.append ((qst [self.scr_mgr ['qmgr'].qmap ['crscode']], qst
                    [self.scr_mgr ['qmgr'].qmap ['qid']]))

                self.pqlen += 1

                self.scr_mgr ['lpqidx'] = self.pqlen - 1
                self.scr_mgr ['pqidx'] = self.scr_mgr ['lpqidx']

            self.qmode = True

            return self.update_qscr (qst)


    
    def update_qscr (self, qst = None, keep_qline = False):

        if not keep_qline:
            self.scr_mgr ['qline'] = 0


        if qst: 
            
            self.scr_mgr ['qst'] = qst
            self.scr_mgr ['optmap'] = []

            self.scr_mgr ['qscr'].move (0, 0)
            self.scr_mgr ['qscr'].clear ()

            for f in ['qdescr'] + ['opt' + chr (97 + i) for i in range (len (self.scr_mgr ['qmgr'].pseudos))]:
                if f.startswith ('opt'):
                    i = (ord (f[-1]) & 0x1f) - 1
                    x = self.scr_mgr ['qscr'].getyx ()
                    
                    if isinstance (self.scr_mgr ['qmgr'].pseudos [i], int):
                        self.scr_mgr ['qscr'].addch (self.scr_mgr ['qmgr'].pseudos [i])
                        pre = ''
                    else:
                        pre = self.scr_mgr ['qmgr'].pseudos [i] + ': '

                    self.scr_mgr ['qscr'].addstr (pre + qst [self.scr_mgr ['qmgr'].qmap [f]].strip ())
                    cur = self.scr_mgr ['qscr'].getyx ()
                    self.scr_mgr ['optmap'].append ([
                        x[0],
                        (cur [0] - x[0]) * (self.scr_mgr.scrdim [1]) + cur [1],
                        self.scr_mgr ['qmgr'].pseudos [i] if isinstance (self.scr_mgr ['qmgr'].pseudos [i], int) else None,
                        curses.A_NORMAL
                        ])

                    self.scr_mgr ['qscr'].addch ('\n')

                elif f == 'qdescr':
                    if isinstance (qst [self.scr_mgr ['qmgr'].qmap ['qn']], int):
                        self.scr_mgr ['qscr'].addch (self.scr_mgr ['qmgr'].pseudos [i])
                        pre = ''
                    else:
                        pre = str (qst [self.scr_mgr ['qmgr'].qmap ['qn']]) + '. '

                    self.scr_mgr ['qscr'].addstr (pre + qst [self.scr_mgr ['qmgr'].qmap [f]].strip () + '\n')

                self.scr_mgr ['qscr'].addch ('\n')

            if not self.scr_mgr ['optmap']:
                pass #NOTE: Draw a textbox for fill-in-the-gap answer
           

            elif qst [self.scr_mgr ['qmgr'].qmap ['qid']] != 'error':

                a = qst [self.scr_mgr ['qmgr'].qmap ['ans']]
                
                if a:
                    i = self.scr_mgr ['qmgr'].pseudos.index (a)

                    self.scr_mgr ['optmap'] [i][-1] = curses.A_BLINK

                else:
                    i = 0

            else:
                    i = 0

            self.paint (self.scr_mgr ['optmap'] [i])

        elif self.scr_mgr ['qst']:
            pass

        else:
            self.scr_mgr ['qline'] = 0
            self.scr_mgr ['qscr'].clear ()
            self.scr_mgr ['qscr'].addstr (0, 0, 'Hit Enter to start')


        self.scr_mgr ['qscr'].noutrefresh (self.scr_mgr ['qline'], 0, self.scr_mgr.scord[0], self.scr_mgr.scord [1],
                (self.scr_mgr.scrdim [0] + self.scr_mgr.scord [0]) - 1, (self.scr_mgr.scrdim [1] + self.scr_mgr.scord
                    [1]) - 1)

        return

    def ctrl_l12 (self):
        if self.qmode and self.scr_mgr ['qst']:
            curses.flash ()
            self.update_qscr ()

    def ctrl_c3 (self):
        return BREAK

    def key_resize410 (self):
        curses.update_lines_cols ()

        self.stdscr.resize (curses.LINES, curses.COLS)

        r = self.scr_mgr.resize (self.stdscr)
        if r and r != -1:
            for scr, inc in r:
                self.update_qscr (
                        scr ['qst'] if not inc else None,
                        keep_qline = True if inc else False)

            return inc

        else:
            return r

    def ctrl_w23 (self):
        self ['keypad'] (True)
        c = self ['getch'] ()

        if c == curses.KEY_UP or c == curses.KEY_LEFT:
            self.scr_mgr.scroll_up ()
            self.update_qscr (keep_qline = True)

        elif c == curses.KEY_DOWN or c == curses.KEY_RIGHT:
            self.scr_mgr.scroll_down ()
            self.update_qscr (keep_qline = True)


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
        if self.qmode and self.scr_mgr ['qst']:
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
        if not subtrahend or not subtrahend.isdigit ():
            subtrahend = 1
        else:
            subtrahend = int (subtrahend.decode())

        qst = self.scr_mgr ['qst'].copy ()
        n = math.trunc (int (qst [self.scr_mgr ['qmgr'].qmap ['qn']] + '0') / 10) - subtrahend

        qst [self.scr_mgr ['qmgr'].qmap ['qn']] = str (n)

        self.update_qscr (qst, keep_qline = False)

    def key_plus43 (self, addend = None):
        if not addend or not addend.isdigit ():
            addend = 1
        else:
            addend = int (addend.decode())

        qst = self.scr_mgr ['qst'].copy ()
        n = math.trunc (int (qst [self.scr_mgr ['qmgr'].qmap ['qn']] + '0') / 10) + addend

        qst [self.scr_mgr ['qmgr'].qmap ['qn']] = str (n)

        self.update_qscr (qst, keep_qline = False)


    def key_plus42 (self, addend = None):
        if not addend or not addend.isdigit ():
            addend = 1
        else:
            addend = int (addend.decode())

        qst = self.scr_mgr ['qst'].copy ()
        n = math.trunc (int (qst [self.scr_mgr ['qmgr'].qmap ['score']] + '0') / 10) + addend

        qst [self.scr_mgr ['qmgr'].qmap ['score']] = str (n)

        self.update_qscr (qst, keep_qline = False)


    def keys_minus47 (self, subtrahend = None):
        if not subtrahend or not subtrahend.isdigit ():
            subtrahend = 1
        else:
            subtrahend = int (subtrahend.decode())

        qst = self.scr_mgr ['qst'].copy ()
        n = math.trunc (int (qst [self.scr_mgr ['qmgr'].qmap ['score']] + '0') / 10) - subtrahend

        qst [self.scr_mgr ['qmgr'].qmap ['score']] = str (n)

        self.update_qscr (qst, keep_qline = False)


def main (stdscr, args):


    mp = configparser.ConfigParser (interpolation =
        configparser.ExtendedInterpolation ())

    mp.read (args.wmap)

    args.wmap = mp

    qmap = mp ['qmap']
    
    curses.start_color ()

    curses.noecho ()
   
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


    if args.updatedb:
        f = open (args.qstdump, 'w') if args.debug else None
        dbmgt.DbMgt.update_hacktab (args.database, ansmgr.iter_cache (), ansmgr.qmap,
                ansmgr._cur, f)

    if ansmgr._cur:
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

    parser.add_argument ('--noupdatedb', '-nodb', action = 'store_false', dest =
            'updatedb', default = True, help = 'Update the database in use')


    parser.add_argument ('--url', help = 'The remote url if no local server',
            action = 'append', required = True)

    parser.add_argument ('--matno', help = 'Your Matric Number', action = 'append')

    parser.add_argument ('--pwd', help = 'Your password',
            action = 'append')

    parser.add_argument ('--crscode', help = 'Your target course', action = 'append')

    parser.add_argument ('--tma', help = 'Your target TMA for the chosen course', action = 'append')


    args = parser.parse_args()
   

    try:
        
        stdscr = curses.initscr ()

        main (stdscr, args)

    except BaseException as err:
        curses.endwin ()
        raise err


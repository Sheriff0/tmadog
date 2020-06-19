divert(1)dnl`'include(`config.m4')dnl
changequote(`£', `%')dnl
import math
import re
import requests
import navigation
import qstmgt
import ansmgt
import dbmgt
import curses
import curses.ascii
import lxml
import qscreen
import copy
import pdb
import json
import cloudscraper
import cookie_parse
import dogs

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

class Interface:
    def __init__ (
            self,
            keys,
            amgr,
ifelse(CONFIG_IF_CURSES, £%, IF_CURSES, CONFIG_IF_CURSES, £1%, IF_CURSES,
£dnl
	    ):
%)dnl
        self.keys = keys
        self.pq = []
        self.navtab = self.keys.navtab
        self.pqlen = 0
        self.boot ()
        self.keys.print = self.printi
        self.status (1)
        self.need_status = False
        self.update_qscr ()

    def echo (self, msg):
ifelse(CONFIG_IF_CURSES, £%, IF_CURSES_ECHO, CONFIG_IF_CURSES, £1%, IF_CURSES_ECHO, £%)dnl

    def getstr (self, prompt = ''):
        self.cmdscr.move (self.LINES - 1, 0)
        self.cmdscr.clrtoeol ()
        self.cmdscr.touchline (0, self.LINES - 1, False)
        curses.curs_set (1)
        self.cmdscr.refresh ()
        curses.def_prog_mode()
        curses.reset_shell_mode ()
        try:
            res = input ("\033[4;37m" + prompt + "\033[0;0m")
        except KeyboardInterrupt:
            print ('')
            res = None

        curses.reset_prog_mode ()
        curses.curs_set (0)
        return res
    
    def change_key99 (self):
        crscode = self.getstr ('Course Code: ')
        
        tma = self.getstr ('Tma No(1-3): ')
            
        if crscode and re.fullmatch (r'\w+', crscode):
            self.scr_mgr [self.keys.CRSCODE] = crscode

        if tma and re.fullmatch (r'\w+', tma):
            self.scr_mgr [self.keys.TMA] = tma
            
        self.boot (self.scr_mgr)
        self.scr_mgr ['qst'] = None

        self.update_qscr ()

    def login_keyL76 (self):
        pass

    def login_keyl108 (self, qscr = None):
        if not qscr or isinstance (qscr, bytearray):
            qscr = self.scr_mgr

        matno = self.getstr ('Matric No: ')
        pwd = self.getstr ('Password: ')
        crscode = self.getstr ('Course Code: ')
        tma = self.getstr ('Tma No(1-3): ')
        self.shutdown (qscr)

        if (not matno or re.fullmatch (matno, qscr [self.keys.UID], flags =
            re.I)) and (not crscode or re.fullmatch (crscode, qscr
                [self.keys.CRSCODE], flags = re.I)) and (not tma or re.fullmatch (tma, qscr
                    [self.keys.TMA], flags = re.I)):
            qscr ['nav']['tma_page']
        else:
            if matno and re.fullmatch (r'\w+', matno):
                qscr [self.keys.UID] = matno

            if pwd and re.fullmatch (r'\w+', pwd):
                qscr [self.keys.PWD] = pwd

            if crscode and re.fullmatch (r'\w+', crscode):
                qscr [self.keys.CRSCODE] = crscode

            if tma and re.fullmatch (r'\w+', tma):
                qscr [self.keys.TMA] = tma
            
            self.boot (qscr)
            qscr ['qst'] = None


define(£COOKIE_KEY$,
£dnl
    def updateCookie_keyAmp38 (self, path = bytearray (), qscr = None):
        if not qscr:
            qscr = self.scr_mgr
        
        if not path:
            path = self.getstr ('Enter cookie filename: ')
        else:
            path = path.decode ()

        qscr [self.keys.COOKIES] = path if path else qscr [self.keys.COOKIES] 
        self.echo ('Reading cookie file')
        try:
            session = self.keys.mksess (qscr [self.keys.URL], path)
            self.echo ('Installing cookie')
            qscr ['nav'].session = session
            self.echo ('Done.')

        except BaseException as err:
            self.printi ('%s: %s' % (path, err.args [1]))

%)dnl
dnl
ifelse(CONFIG_COOKIE_KEY, £%, COOKIE_KEY, CONFIG_COOKIE_KEY, £1%, COOKIE_KEY, £%)dnl

    def shutdown (self, qscr = None):
        if not qscr:
            qscr = self.scr_mgr

        if self.bootable (qscr):
            return -1

        return qscr ['nav']['logout_page']

    def boot (self, qscr = None):
        if not qscr:
            qscr = self.scr_mgr

        try:
            self.printi ('Looking for existing navigator for %s' % (qscr [self.keys.UID],))

            idx = self.navtab.index (qscr [self.keys.UID], attr = 'refcount')
            qscr ['nav'] = self.navtab [idx]
            self.printi ('Found. Reused found navigator')

        except ValueError:

            self.printi ('Not Found. Configuring a new navigator')
            nav = navigation.Navigator (
                    qscr [self.keys.URL],
                    qscr [self.keys.WMAP],
                    qscr, #dangerous maybe
                    session = qscr [self.keys.SESSION]
                    )

            qscr ['nav'] = nav

            self.printi ('Done.')

            nav.refcount = qscr [self.keys.UID]

            self.navtab.append (nav)

        self.printi ('Login in user %s' % (qscr [self.keys.UID],))

        qscr ['qmgr'] = QstMgt.QstMgr (
                nav = qscr ['nav'],
                matno = qscr [self.keys.UID],
                crscode = qscr [self.keys.CRSCODE],
                tma = qscr [self.keys.TMA],
                stop = 10,
                qmap = qscr [self.keys.WMAP]['qmap'],
                )

        qscr ['qline'] = 0
        qscr ['optmap'] = []
        qscr ['pqidx'] = None
        qscr ['lpqidx'] = None
        qscr ['qst'] = None
        qscr ['qmode'] = False
        qscr ['qmgr'].interactive = True

        self.printi ('Done.')
        return qscr ['qmgr']


    def __call__ (self, key):

        args = bytearray ()
        comm = self._get_cmd (key)

        if not comm:
            self.stdscr.scrollok (True)
            self.stdscr.keypad (True)
            self.stdscr.nodelay (False)
            self.stdscr.notimeout (False)
            self.stdscr.move (self.LINES - 1, 0)
            self.stdscr.clrtoeol ()
            self.stdscr.touchline (0, self.LINES - 1, False)
            curses.ungetch (key)
            self.stdscr.echochar (key)
            curses.echo ()

        while not comm:
            c = self.stdscr.getch ()
            comm = self._get_cmd (c)
            if comm:
                pass
            elif c == curses.ascii.ESC:
                break

            elif curses.ascii.isascii (c):
                args.append (c)

            else:
                break
        else:
            curses.noecho ()
            self.ctrl_l12 ()
            return comm (args) if args else comm ()


        curses.noecho ()
        self.ctrl_l12 ()


    def _get_cmd (self, key):
        cmd = (getattr (self, k) for k in type (self).__dict__ if re.search
                (r'(?<!\d)' + str (key) + r'(?!\d)', k))

        try:
            comm = next (cmd)
            return comm

        except StopIteration:
            return None


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
                vis, trange, *misc = self.visibility (t)

                if vis & UNCAPTURED:
                    offset = t[0] - (self.scr_mgr ['qline'] + misc [1])
                    self.scr_mgr ['qline'] += offset

                elif vis & TOP:

                    t = n [0] - subtrahend

                    t = self.scr_mgr ['optmap'] [t]

                    vis, trange, *misc = self.visibility (t)
                    if vis & ABOVE:
                        self.scr_mgr ['qline'] = trange [-1]

                else:
                    self.scr_mgr ['qline'] -= subtrahend


            except IndexError:
                t = self.scr_mgr ['optmap'] [0]
                vis, trange, *misc = self.visibility (t)
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

        self.doupdate ()

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
                vis, trange, *misc = self.visibility (t)

                if vis & ABOVE:
                    self.scr_mgr ['qline'] = trange [-1]

                elif vis & BOTTOM:
                    t = self.scr_mgr ['optmap'] [n [0] + addend]

                    vis, trange, *misc = self.visibility (t)
                    if vis & BELOW:
                        self.scr_mgr ['qline'] = trange [0]


                else:
                    self.scr_mgr ['qline'] += addend


            except IndexError:
                t = self.scr_mgr ['optmap'] [-1]
                vis, trange, *misc = self.visibility (t)

                if vis & UNCAPTURED:
                    self.scr_mgr ['qline'] = trange [0]

                else:
                    self.scr_mgr ['qline'] += addend

            tl = self.scr_mgr ['optmap'] [-1]
            visl, trangel, *misc = self.visibility (tl)
            bot_scry = misc [1]
            if bot_scry > trangel [-1]:
                self.scr_mgr ['qline'] -= (bot_scry - trangel [-1])

            self.paint (undo = True)

            self.scr_mgr ['qscr'].move (t[0], 0)
            self.paint ()


        elif not self.scr_mgr ['qmode']:
            if hasattr (self, 'msgyx') and self.msgyx:
                self.scr_mgr ['qline'] += addend
                vis, trange, *misc = self.visibility (self.msgyx)

                bot_scry = misc [1]

                if bot_scry > trange [-1]:
                    self.scr_mgr ['qline'] -= (bot_scry - trange [-1])


        if self.scr_mgr ['qline'] < 0:
            self.scr_mgr ['qline'] = 0

        self.doupdate ()


    def visibility (self, coord):
        flags = 0

        topy = coord [0]

        boty = math.ceil (coord [1] / self.scr_mgr.scrdim [1]) + topy - 1


        bot_scry = (self.scr_mgr ['qline'] + (self.scr_mgr.scrdim [0] -
                self.saloc)) - 1

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

        return (flags, txt_range, top_scry, bot_scry, topy, boty)


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

        self.doupdate ()

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

            self.doupdate ()

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


        self.doupdate ()

        return

    def ctrl_l12 (self, *args):
        #curses.flash ()
        self.stdscr.clear ()
        self.overwrite (self.scr_mgr ['qscr'], self.stdscr, self.scr_mgr ['qline'], 0, self.scr_mgr.scord[0], self.scr_mgr.scord [1],
        (self.scr_mgr.scrdim [0] + self.scr_mgr.scord [0]) - 1 - self.saloc, (self.scr_mgr.scrdim [1] + self.scr_mgr.scord
            [1]) - 1)
        
        self.status (1)
        self.stdscr.clearok (True)
        self.stdscr.noutrefresh ()
        curses.doupdate ()

    def ctrl_c3 (self, *args):
        return BREAK

    def key_resize410 (self):
        curses.update_lines_cols ()

        self.stdscr.resize (curses.LINES, curses.COLS)
        self.LINES, self.COLS = self.stdscr.getmaxyx ()
        self.cmdscr = curses.newwin (self.LINES, self.COLS)

        r = self.scr_mgr.resize (self.stdscr)
        if r and r != -1:
            for scr, inc in r:
                self.update_qscr (
                        scr ['qst'] if not inc else None,
                        flags = PRT_PRINT_CHOICES | PRT_PRINT_QST | PRT_KEEPLINE if inc else PRT_PRINT_QST | PRT_PRINT_CHOICES)
            self.status (1)
            self.doupdate ()
            return inc

        else:
            return r

    def ctrl_w23 (self, offset = b'1'):
        if not offset.isdigit ():
            return

        offset = int (offset.decode ())
        self ['keypad'] (True)
        c = self ['getch'] ()

        self.status (0)
        self.doupdate ()

        if c == curses.KEY_UP or c == curses.KEY_LEFT:
            self.scr_mgr.scroll (-offset)

        elif c == curses.KEY_DOWN or c == curses.KEY_RIGHT:
            self.scr_mgr.scroll (offset)


        if self.bootable ():
            self.boot ()
        #____________________looks dumb
        f = self.need_status#|___ 
        self.need_status = False#|_______________
        self.update_qscr (flags = PRT_KEEPLINE)#|_____________________
        self.need_status = f#|

    def status (self, highlight = True):
        if not hasattr (self, 'saloc'):#FIXME: Get rid!
            self.saloc = 2 if self.scr_mgr.scrdim [0] > 2 else 0

        if self.saloc:
            self.stdscr.move (self.scr_mgr.scord [0] + self.scr_mgr.scrdim [0] -
                    self.saloc, 0)
            self.stdscr.clrtoeol ()
            self.stdscr.addnstr (self.scr_mgr.scord [0] + self.scr_mgr.scrdim [0] - self.saloc, 0,
                    '%s %s TMA%s' % (self.scr_mgr [self.keys.UID].upper (),
                        self.scr_mgr [self.keys.UID1].upper (), self.scr_mgr
                        [self.keys.UID2]), self.scr_mgr.scrdim [1])
            self.stdscr.chgat (self.scr_mgr.scord [0] + self.scr_mgr.scrdim [0]
                    - self.saloc, 0 ,
                    curses.A_REVERSE | (curses.A_BOLD if highlight else 0))


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


    def decreaseQn_keyMinus45 (self, subtrahend = None):
        if self.scr_mgr ['qmode'] and self.scr_mgr ['qst']:
            if not subtrahend or not subtrahend.isdigit ():
                subtrahend = 1
            else:
                subtrahend = int (subtrahend.decode())

            qst = self.scr_mgr ['qst'].copy ()
            n = math.trunc (int (qst [self.scr_mgr ['qmgr'].qmap ['qn']] + '0') / 10) - subtrahend

            qst [self.scr_mgr ['qmgr'].qmap ['qn']] = str (n)

            self.update_qscr (qst, flags = PRT_PRINT_CHOICES | PRT_PRINT_QST | PRT_KEEPLINE)

    def increaseQn_keyPlus43 (self, addend = None):
        if self.scr_mgr ['qmode'] and self.scr_mgr ['qst']:
            if not addend or not addend.isdigit ():
                addend = 1
            else:
                addend = int (addend.decode())

            qst = self.scr_mgr ['qst'].copy ()
            n = math.trunc (int (qst [self.scr_mgr ['qmgr'].qmap ['qn']] + '0') / 10) + addend

            qst [self.scr_mgr ['qmgr'].qmap ['qn']] = str (n)

            self.update_qscr (qst, flags = PRT_PRINT_CHOICES | PRT_PRINT_QST | PRT_KEEPLINE)


    def increaseTotscrore_keyAsterik42 (self, addend = None):
        if self.scr_mgr ['qmode'] and self.scr_mgr ['qst']:
            if not addend or not addend.isdigit ():
                addend = 1
            else:
                addend = int (addend.decode())

            qst = self.scr_mgr ['qst'].copy ()
            n = math.trunc (int (qst [self.scr_mgr ['qmgr'].qmap ['score']] + '0') / 10) + addend

            qst [self.scr_mgr ['qmgr'].qmap ['score']] = str (n)

            self.update_qscr (qst, flags = PRT_PRINT_CHOICES | PRT_PRINT_QST | PRT_KEEPLINE)


    def decreaseTotscore_keyFslash47 (self, subtrahend = None):
        if self.scr_mgr ['qmode'] and self.scr_mgr ['qst']:
            if not subtrahend or not subtrahend.isdigit ():
                subtrahend = 1
            else:
                subtrahend = int (subtrahend.decode())

            qst = self.scr_mgr ['qst'].copy ()
            n = math.trunc (int (qst [self.scr_mgr ['qmgr'].qmap ['score']] + '0') / 10) - subtrahend

            qst [self.scr_mgr ['qmgr'].qmap ['score']] = str (n)

            self.update_qscr (qst, flags = PRT_PRINT_CHOICES | PRT_PRINT_QST | PRT_KEEPLINE)


    def chCrscode_keyCaret94 (self, crscode = bytearray ()):
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

    def discoverAns_keyQuotemark33 (self, mod = bytearray ()):
        if self.scr_mgr ['qmode'] and self.scr_mgr ['qst']:


            matno = 'Nou123456789'

            try:
                mod = 0 if not mod else int (mod.decode ()) - 1

            except ValueError:
                return

            def mask (dic, pat, sub):
                dic1 = requests.structures.OrderedDict ()
                for k, v in dic.items ():
                    if isinstance (v, str):
                        v = re.sub (r'(?P<cs>' + pat + ')',
                                self.scr_mgr ['qmgr']._copycase (sub), v, flags =
                                re.I)
                    dic1 [k] = v

                return dic1


            count = 0

            qst = self.scr_mgr ['qst']
            c = self ['instr'] (len (self.scr_mgr ['qmgr'].pseudos [0]))

            c = c.decode ()

            qst [self.scr_mgr ['qmgr'].qmap ['ans']] = c

            while mod: #Answer Discovery loop
                self.echo ('Trying to discover answer to question %s, Please wait...' % (qst
                    [self.scr_mgr ['qmgr'].qmap ['qn']],))

                qst1 = mask (qst, self.scr_mgr [self.keys.UID], matno)

                for a in dogs.AnyheadList (self.scr_mgr ['qmgr'].pseudos, qst1 [self.scr_mgr ['qmgr'].qmap ['ans']]):

                    qst1 [self.scr_mgr ['qmgr'].qmap ['ans']] = a

                    try:
                        e = self.scr_mgr ['qmgr'].submit (qst1)

                        x = re.search (r'(?P<mark>[01])\s*' + self.scr_mgr ['nav'].webmap ['fb']['on_qst_submit'].strip (), self.scr_mgr ['qmgr'].sres.text, re.I)

                        if x:
                            x = int (x.group ('mark'))
                            self.amgr.check (qst1, x, e)
                            if x == 1:
                                qst [self.scr_mgr ['qmgr'].qmap ['ans']] = a

                                self.echo ('Done. Unmasking %s for submission' % (self.scr_mgr [self.keys.UID],))
                                e = self.scr_mgr ['qmgr'].submit (qst)

                                x = re.search (r'(?P<mark>[01])\s*' + self.scr_mgr ['nav'].webmap ['fb']['on_qst_submit'].strip (), self.scr_mgr ['qmgr'].sres.text, re.I)

                                if not x or int (x.group ('mark')) == 0:
                                    raise TypeError ()
                                self.echo ('Done.')
                                break

                        else:
                            self.echo ('Error.')
                            raise TypeError ()
                    except:
                        return self.message (self.scr_mgr ['qmgr'].sres) if hasattr (self.scr_mgr ['qmgr'], 'sres') else None

                qst = self.scr_mgr ['qmgr'].fetch (timeout = (30.5, 60))

                if not qst or not isinstance (qst, lxml.html.FieldsDict):
                    return self.message (self.scr_mgr ['qmgr'].qres) if hasattr (self.scr_mgr ['qmgr'], 'qres') else None

                x = copy.deepcopy (qst)

                x = self.amgr.answer (x)

                if x and x != self.amgr.NOANSWER and qst [self.scr_mgr ['qmgr'].qmap ['qid']] == x [self.scr_mgr ['qmgr'].qmap ['qid']]:
                    qst = x

                self.pq.append ((qst [self.scr_mgr ['qmgr'].qmap ['crscode']], qst
                    [self.scr_mgr ['qmgr'].qmap ['qid']]))

                self.pqlen += 1

                self.scr_mgr ['lpqidx'] = self.pqlen - 1
                self.scr_mgr ['pqidx'] = self.scr_mgr ['lpqidx']

                self.echo ('Done.')
                count += 1
                mod -= 1


            qst1 = mask (qst, self.scr_mgr [self.keys.UID], matno)

            if count == 0:

                self.update_qscr (qst1, flags = PRT_PRINT_QST | PRT_KEEPLINE | PRT_KEEPCUR, qpaint = curses.A_DIM)

            else:
                self.update_qscr (qst1, qpaint = curses.A_DIM)

            curses.flushinp() #For safety

    def overwrite (self, scr, dest, srow, scol, dminrow, dmincol, dmaxrow,
            dmaxcol):
        srow = 0 if srow < 0 else srow
        dminrow = 0 if dminrow < 0 else dminrow
        sp = scr.getyx ()
        dp = dest.getyx ()
        for off, row in enumerate (range (dminrow, dmaxrow + 1)):
            for off1, col in enumerate (range (scol, scol + (dmaxcol - dmincol +
                1))):
                ch = scr.inch (srow + off, col)
                dest.addch (row, dmincol + off1, ch)

        scr.move (*sp)
        dest.move (*dp)


    def doupdate (self):
        self.overwrite (self.scr_mgr ['qscr'], self.stdscr, self.scr_mgr ['qline'], 0, self.scr_mgr.scord[0], self.scr_mgr.scord [1],
                (self.scr_mgr.scrdim [0] + self.scr_mgr.scord [0]) - 1 - self.saloc, (self.scr_mgr.scrdim [1] + self.scr_mgr.scord
                    [1]) - 1)

        if self.need_status:
            self.status (1)

        self.stdscr.noutrefresh ()
        return curses.doupdate ()
ifelse(TMADOG_IF, £%, £%, ££divert(1)%%)

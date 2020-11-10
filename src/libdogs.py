import math
import re
import requests
import navigation
import qstm
import ansm
import dbm
import lxml
import scrm
import copy
import pdb
import json
import cloudscraper
import cookie_parse
import dogs
import os
import sys
import builtins 
import pathlib

## NOTE: assigning to this ain't thread-safe, thus all functions should return their
## caugth errors where possible.

class errno(BaseException):
    def __init__(self, *pargs, **kwargs):
        super ().__init__ (*pargs, **kwargs);

    def __bool__(self):
        return False;

    def __eq__(self, value):
        if value == False or value == None:
            return True;
        else:
            return False;

    def echo (self, msg):
        if not hasattr (self, "echopad"):
            self.echopad = curses.newpad (50, 1000)
            self.echopad.scrollok (True)

        self.echopad.clear ()
        self.echopad.addstr (0, 0, msg)
        self.echopad.noutrefresh (0, 0, self.LINES - 1, 0, self.LINES - 1, self.COLS - 1)
        self.doupdate ()


    def change_keyc99 (self):
        crscode = self.getstr ("Course Code: ")

        tma = self.getstr ("Tma No(1-3): ")

        if crscode and re.fullmatch (r"\w+", crscode):
            self.scr_mgr [self.keys.CRSCODE] = crscode

        if tma and re.fullmatch (r"\w+", tma):
            self.scr_mgr [self.keys.TMA] = tma

        self.boot (self.scr_mgr)
        self.scr_mgr ["qst"] = None

        self.update_qscr ()

    def login_keyL76 (self):
        pass

def logout(nav):
    try:
        nav["logout_page"];
        return True;
    except BaseException as err:
        return errno("logout err", err);

def tlogin (nav, key):
   """ login function that that sees a different profile_page""" 
    s = logout (nav);

    if not s:
        return s;
    
    try:
        nav["tma_page"];
        return True;
    except BaseException as err:
        s = logout(nav);
        if not s:
            return errno(s, err);
        else:
            return errno(err);



    def updateCookie_keyAmp38 (self, path = bytearray (), qscr = None):
        if not qscr:
            qscr = self.scr_mgr

        if not path:
            path = self.getstr ("Enter cookie filename: ")
        else:
            path = path.decode ()

        if path:
            self.echo ("Reading cookie file")
            try:
                self.echo ("Installing cookie")
                session = self.keys.mksess (qscr [self.keys.URL], path)

            except BaseException as err:
                self.printi ("%s: %s" % (path, err.args [1]), PRINT_ERR)

            else:
                qscr ["nav"].session = session
                qscr [self.keys.COOKIES] = path
                self.echo ("Done.")


def create_nav(key):

    self.nav = navigation.Navigator (
            self.prep_argv[cli]["url"],
            self.prep_argv[cli]["wmap"],
            self.prep_argv[cli],
            session = None, #NOTE create a new session
            );

    def bootable (self, qscr = None):
        if not qscr:
            qscr = self.scr_mgr

        return "nav" not in qscr or "qmgr" not in qscr or not qscr ["nav"] or not qscr ["qmgr"]

    def shutdown (self, qscr = None):
        if not qscr:
            qscr = self.scr_mgr

        if self.bootable (qscr):
            return -1

        return qscr ["nav"]["logout_page"]

    def boot (self, qscr = None):
        if not qscr:
            qscr = self.scr_mgr

        try:
            self.printi ("Looking for existing navigator for %s" % (qscr [self.keys.UID],))

            idx = self.navtab.index (qscr [self.keys.UID], attr = "refcount")
            qscr ["nav"] = self.navtab [idx]
            self.printi ("Found. Reused found navigator")

        except ValueError:

            self.printi ("Not Found. Configuring a new navigator")
            nav = navigation.Navigator (
                    qscr [self.keys.URL],
                    qscr [self.keys.WMAP],
                    qscr, #dangerous maybe
                    session = qscr [self.keys.SESSION]
                    )

            qscr ["nav"] = nav

            self.printi ("Done.")

            nav.refcount = qscr [self.keys.UID]

            self.navtab.append (nav)

        self.printi ("Login in user %s" % (qscr [self.keys.UID],))

        qscr ["qmgr"] = qstm.QstMgr (
                nav = qscr ["nav"],
                matno = qscr [self.keys.UID],
                crscode = qscr [self.keys.CRSCODE],
                tma = qscr [self.keys.TMA],
                stop = 10,
                qmap = qscr [self.keys.WMAP]["qmap"],
                )

        qscr ["qline"] = 0
        qscr ["optmap"] = []
        qscr ["pqidx"] = None
        qscr ["lpqidx"] = None
        qscr ["qst"] = None
        qscr ["qmode"] = False
        qscr ["qmgr"].interactive = True

        self.printi ("Done.")
        return qscr ["qmgr"]


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
            return comm (args) if args else comm ()


        curses.noecho ()
        self.ctrl_l12 ()

    def _get_cmd (self, key):
        cmd = (getattr (self, k) for k in type (self).__dict__ if re.search
                (r"(?<!\d)" + str (key) + r"(?!\d)", k))

        try:
            comm = next (cmd)
            return comm

        except StopIteration:
            return None


    def key_left260 (self, subtrahend = b"1"):
        if self.scr_mgr ["lpqidx"] != None and self.scr_mgr ["pqidx"] != None and self.scr_mgr ["qmode"] and self.pq:

            if not subtrahend.isdigit ():
                return

            subtrahend = int (subtrahend.decode())

            l = self.amgr (*self.pq [self.scr_mgr ["lpqidx"]])

            self.scr_mgr ["pqidx"] -= subtrahend

            if 0 <= self.scr_mgr ["pqidx"] < self.pqlen:
                    p = self.amgr (*self.pq [self.scr_mgr ["pqidx"]])

                    if p and l:
                        self.update_qscr (self.amgr.download (p, l))

                    else:
                        pass #pdb.set_trace ()

            elif self.scr_mgr ["pqidx"] < 0:
                self.scr_mgr ["pqidx"] = 0


    def key_right261 (self, addend = b"1"):
        if self.scr_mgr ["lpqidx"] != None and self.scr_mgr ["pqidx"] != None and self.scr_mgr ["qmode"] and self.pq:
            l = self.amgr (*self.pq [self.scr_mgr ["lpqidx"]])

            if not addend.isdigit ():
                return

            addend = int (addend.decode())

            self.scr_mgr ["pqidx"] += addend

            if 0 <= self.scr_mgr ["pqidx"] < self.pqlen:
                p = self.amgr (*self.pq [self.scr_mgr ["pqidx"]])

                if p and l:
                    self.update_qscr (self.amgr.download (p, l))

                else:
                    pass #pdb.set_trace ()

            elif self.scr_mgr ["pqidx"] >= self.pqlen:
                self.scr_mgr ["pqidx"] = self.pqlen

                if l != self.scr_mgr ["qst"]:
                    self.update_qscr (self.amgr.download (l, self.scr_mgr ["qst"]))


    def key_up259 (self, subtrahend = b"1"):
        if not subtrahend.isdigit ():
            return

        subtrahend = int (subtrahend.decode())

        if self.scr_mgr ["qmode"] and self.scr_mgr ["optmap"]:
            cur = self.scr_mgr ["qscr"].getyx ()
            n = [i for i,t in enumerate (self.scr_mgr ["optmap"]) if t[0] == cur [0]]

            if not n:
                return

            try:
                if (n [0] - subtrahend) < 0:
                        raise IndexError (n [0] - subtrahend)


                t = self.scr_mgr ["optmap"] [n [0]]
                vis, trange, *misc = self.visibility (t)

                if vis & UNCAPTURED:
                    offset = t[0] - (self.scr_mgr ["qline"] + misc [1])
                    self.scr_mgr ["qline"] += offset

                elif vis & TOP:

                    t = n [0] - subtrahend

                    t = self.scr_mgr ["optmap"] [t]

                    vis, trange, *misc = self.visibility (t)
                    if vis & ABOVE:
                        self.scr_mgr ["qline"] = trange [-1]

                else:
                    self.scr_mgr ["qline"] -= subtrahend


            except IndexError:
                t = self.scr_mgr ["optmap"] [0]
                vis, trange, *misc = self.visibility (t)
                if vis & ABOVE:
                    self.scr_mgr ["qline"] = trange [-1]

                else:
                    self.scr_mgr ["qline"] -= subtrahend

            self.paint (undo = True)

            self.scr_mgr ["qscr"].move (t[0], 0)
            self.paint ()

        elif not self.scr_mgr ["qmode"]:
            self.scr_mgr ["qline"] -= subtrahend


        if self.scr_mgr ["qline"] < 0:
            self.scr_mgr ["qline"] = 0

        self.doupdate ()

    def key_down258 (self, addend = b"1"):
        if not addend.isdigit ():
            return

        addend = int (addend.decode())

        if self.scr_mgr ["qmode"] and self.scr_mgr ["optmap"]:
            cur = self.scr_mgr ["qscr"].getyx ()
            n = [i for i,t in enumerate (self.scr_mgr ["optmap"]) if t[0] == cur [0]]

            if not n:
                return

            try:
                self.scr_mgr ["optmap"] [n [0] + addend]
                t = self.scr_mgr ["optmap"] [n [0]]
                vis, trange, *misc = self.visibility (t)

                if vis & ABOVE:
                    self.scr_mgr ["qline"] = trange [-1]

                elif vis & BOTTOM:
                    t = self.scr_mgr ["optmap"] [n [0] + addend]

                    vis, trange, *misc = self.visibility (t)
                    if vis & BELOW:
                        self.scr_mgr ["qline"] = trange [0]


                else:
                    self.scr_mgr ["qline"] += addend


            except IndexError:
                t = self.scr_mgr ["optmap"] [-1]
                vis, trange, *misc = self.visibility (t)

                if vis & UNCAPTURED:
                    self.scr_mgr ["qline"] = trange [0]

                else:
                    self.scr_mgr ["qline"] += addend

            tl = self.scr_mgr ["optmap"] [-1]
            visl, trangel, *misc = self.visibility (tl)
            bot_scry = misc [1]
            if bot_scry > trangel [-1]:
                self.scr_mgr ["qline"] -= (bot_scry - trangel [-1])

            self.paint (undo = True)

            self.scr_mgr ["qscr"].move (t[0], 0)
            self.paint ()


        elif not self.scr_mgr ["qmode"]:
            if hasattr (self, "msgyx") and self.msgyx:
                self.scr_mgr ["qline"] += addend
                vis, trange, *misc = self.visibility (self.msgyx)

                bot_scry = misc [1]

                if bot_scry > trange [-1]:
                    self.scr_mgr ["qline"] -= (bot_scry - trange [-1])


        if self.scr_mgr ["qline"] < 0:
            self.scr_mgr ["qline"] = 0

        self.doupdate ()

    def visibility (self, coord):
        flags = 0

        topy = coord [0]

        boty = math.ceil (coord [1] / self.scr_mgr.scrdim [1]) + topy - 1


        bot_scry = (self.scr_mgr ["qline"] + (self.scr_mgr.scrdim [0] -
                self.saloc)) - 1

        top_scry = self.scr_mgr ["qline"]

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

class Checker:
    def __init__(self):
        pass

class CookieError(BaseException):
    def __init__(self, *pargs, *kwargs):
        super ().__init__ (*pargs, **kwargs);

def SET_ERRNO_ON_EXCEPT_TO(func, errclass, *pargs, **kwargs):
    global ERRNO;

    try:
        return func(*pargs, **kwargs);
    except BaseException as err:
        ERRNO = errclass(err);
    
    return False;


def SET_ERRNO_ON_EXCEPT(func, *pargs, **kwargs):
    global ERRNO;

    try:
        return func(*pargs, **kwargs);
    except BaseException as err:
        ERRNO = err;

    return False;

def session_from_cookies (self, url, cookie):
    global ERRNO;

    if pathlib.Path(cookie_file).exists():
        with open (cookie_file) as f:
            cookie_str = f.read ();

    else:
        cookie_str = cookie_file;
    
    try:
        cookt = cookie_parse.bake_cookies (cookie_str, url);

    except BaseException as err:
        return errno("can't parse cookies", err);

    if not cookt:
        return errno("No cookies", cookt);

    session = requests.Session ()
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


    return session



def submit (qst, nav, qmgr, c = False):
    
    if c != False:
        qst[qmgr.qmap["ans"]] = c;

    try:
        e = qmgr.submit(qst);
    except BaseException as err:
        return errno(err, qst, qmgr);

    x = re.search (r"(?P<mark>[01])\s*" +
            nav.webmap["fb"]["on_qst_submit"].strip (), qmgr.sres.text,
            re.I);

    if x:
        return int (x.group ("mark"));
    else:
        return errno("No mark", qst, qmgr);

def answer(qst, amgr):
    try:
        x = copy.deepcopy (qst);

        x = amgr.answer (x);

        if x and x != ansm.ANS_NOANSWER and qst [qmgr.qmap ["qid"]] == x [qmgr.qmap ["qid"]]:
            return x;

        return errno(qst, amgr);

    except BaseException as err:
        return errno(qst, amgr);;


def fetch(qmgr):
    global ERRNO;

    try:
        qst = qmgr.fetch (timeout = (30.5, 60));
        if not qst or not isinstance (qst, lxml.html.FieldsDict):
            return errno("no question", qmgr);

        return qst; 
    except BaseException as err:
        return errno(err);


def addqn(qst, qmgr, addend = 1):
        qst = qst.copy ();
        n = math.trunc (int (qst [qmgr.qmap["qn"]] + "0") / 10) + addend;

        qst [qmgr.qmap ["qn"]] = str (n);


def addscrore(qst, qmgr, addend = 1):
            qst = qst.copy ();
            n = math.trunc (int (qst [qmgr.qmap ["score"]] + "0") / 10) + addend;

            qst [qmgr.qmap ["score"]] = str (n)


def ch_crscode(qst, qmgr, crscode = ""):
    out = {};
    for k,v in qst.copy ().items ():
        if isinstance (v, str):
            v = re.sub (r"(?P<cs>" + self.scr_mgr ["crscode"] + ")",
                    self.scr_mgr ["qmgr"]._copycase (crscode), v, flags =
                    re.I)
        out [k] = v

def mask (qst, qmgr, mpat, mvalue):
    dic1 = requests.structures.OrderedDict ()
    for k, v in qst.items ():
        if isinstance (v, str):
            v = re.mvalue (r"(?P<cs>" + mpat + ")",
                    qmgr._copycase (mvalue), v, flags =
                    re.I);
        dic1 [k] = v;

    return dic1;


class Runner:
    def __init__(self, qmgr, amgr, nav, mask, qst = False, mvalue = "Nou123456789"):
        self.qst = qst;
        self.qmgr = qmgr;
        self.amgr = amgr;
        self.nav = nav;
        self.mvalue = mvalue;
        self.mask = mask;

    def start(c = None, count = 1):
        yield from self.__iter__ (c, count);

    def __iter__ (self, c = None, count = 1):

        if isinstance(c, (bytes, bytearray)):
            c = c.decode ();
        
        if not self.qst:
            self.qst = fetch (self.qmgr);
            if self.qst == False:
                yield False;

        self.qst [self.qmgr.qmap ["ans"]] = c;

        while count: #Answer Discovery loop
            qst1 = mask (self.qst, self.qmgr, self.mask, self.mvalue);

            for a in dogs.AnyheadList (self.qmgr.pseudos, qst1 [self.qmgr.qmap ["ans"]]):

                qst1 [self.qmgr.qmap ["ans"]] = a;
                e = submit(qst1, self.nav, self.qmgr);

                if e == 1:
                    self.qst [qmgr.qmap ["ans"]] = a;

                    e = submit (self.qst, self.nav, self.qmgr);


                    if e == 0:
                        ERRNO = AnswerInconsistent(qst1, self.qst);
                        yield False;
                    elif e == 1:
                        yield self.qst.copy();
                    elif e == False:
                        yield False;

                    break;

                elif e == False: #for submit()
                    yield False;

            self.qst = fetch (self.qmgr);
            
            if self.qst == False:
                yield False;

            x = answer(self.qst, self.amgr);
            if x != False:
                self.qst = x;

            count -= 1;

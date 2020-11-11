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

CRSCODE = 'crscode'
TMA = 'tma'
URL = 'url'
WMAP = 'wmap'
COOKIES = 'cookies'
SESSION = 'session'


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


def create_nav(key):
    self.nav = navigation.Navigator (
            self.prep_argv[cli]["url"],
            self.prep_argv[cli]["wmap"],
            self.prep_argv[cli],
            session = None, #NOTE create a new session
            );

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



def preprocess(args):
    print = print

        args = args.__dict__;

        matnos = self.List (args ['matno'])
        pwds = self.List (args ['pwd'])
        crscodes = self.List (args ['crscode'])
        tmas = self.List (args ['tma'])
        cookies = self.List (args ['cookies'])
        urls = self.List (args ['url'])
        wmap = args ['wmap']
        UID = self.wmap ['kmap']['matno']
        UID1 = self.CRSCODE
        UID2 = self.TMA
        PWD = self.wmap ['kmap']['pwd']
        param = {}
        param [self.WMAP] = self.wmap
        len = max (len (self.crscodes), len (self.tmas), len (self.matnos))
        navtab = scrm.QScrList ()

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


def logout(nav):
    try:
        nav["logout_page"];
        return True;
    except BaseException as err:
        return errno("logout err", err);


def login(nav):
    # to make sure we are safe to login. it shouldn't be problematic at all
    # times.
    st = logout(nav);

    if not st:
        return st;

    try:
        nav["profile_page"];
        to, fro = nav('qst_page')[:-1];
        return True;

    except BaseException as err:
        return errno("login err", err);

def unassign(nav):
    return logout(nav);

## this for now, is case-insensitive
def get_key_usr(key):
    return key[USERNAME].lower();

## others are returned "as is"
def get_key_pwd(key):
    return key[PWD];

def get_key_url(key):
    return key[URL];

def get_key_course(key):
    return key[CRSCODE].lower();

def get_key_tma(key):
    return key[TMA];

def get_key_webmap(key):
    return key[WEBMAP];


def reconfigure(nav, usr):
    nav.reconfigure(usr[USERNAME],get_key_webmap(usr), usr);
    return True;


def assign(usr, nav = None):
    if nav == None:
        nav = create_nav(usr);
    
    else:
        if self.get_key_usr(self.nav.keys) != get_key_usr(cli):
            reconfigure(nav, usr);
    # at all times this should'nt be problematic (whether a user is logged in or
    # not)
    unassign(nav);
    login(nav);
    

class Checker:
    def __init__(self):
        pass

class CookieError(BaseException):
    def __init__(self, *pargs, *kwargs):
        super ().__init__ (*pargs, **kwargs);


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

    self.nextq [self.dt1 or self.dt0] = qst

    self.totscore = math.trunc (int (qst [self.qmap ['score']] + '0') / 10)

    kwargs.setdefault (
            'headers',
            dogs.mkheader (self.nextq ['url'], self.referer1)
            )

    self.sres = self.nav.session.request (**self.nextq, **kwargs)

    self.sres.raise_for_status ()
    x = self.nextq.pop (self.dt1 or self.dt0)

    self.referer = self.sres.url
    try:
        res = self.fetch ()

        self.nextq [self.dt1 or self.dt0] = res

        s = (math.trunc (int (res[self.qmap ['score']] + '0') / 10) - self.totscore) == 1

        self.totscore = math.trunc (int (res[self.qmap ['score']] + '0') / 10)

        return int (s)

    except:
        return None

    x = re.search (r"(?P<mark>[01])\s*" +
            nav.webmap["fb"]["on_qst_submit"].strip (), qmgr.sres.text,
            re.I);

    if x:
        return int (x.group ("mark"));
    else:
        return errno("No mark", qst, qmgr);

fetch_t = dict;

F_QUESTION = "qst";
F_REQUEST = "request";
F_QKEY = "data";
F_REFERER = "ref";

def brute_submit(nav, f_type, retry = 3, **kwargs):

    qst = f_type[F_QKEY].copy();

    kwargs.setdefault (
            'headers',
            dogs.mkheader (
                f_type[F_REQUEST]['url'], 
                f_type.get(F_REFERER, "")
                ),
            )

    sres = nav.session.request (**self.nextq, **kwargs)

    self.sres.raise_for_status ()
    x = self.nextq.pop (self.dt1 or self.dt0)

    self.referer = self.sres.url
    try:
        res = self.fetch ()

        self.nextq [self.dt1 or self.dt0] = res

        s = (math.trunc (int (res[self.qmap ['score']] + '0') / 10) - self.totscore) == 1

        self.totscore = math.trunc (int (res[self.qmap ['score']] + '0') / 10)

        return int (s)

    except:
        return None

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

def _transform_req (self, req, matno, tma , crscode):

    tma = str (tma)
    tma = 'tma' + tma if not tma.startswith (('tma', 'Tma', 'TMA')) else tma
    self.dt0 = 'data' if req['method'] in ('POST', 'post') else 'params'
    req['url'] = re.sub (r'(?P<cs>nou)\d{9}', self._copycase (matno), req['url'], flags = re.IGNORECASE)

    req['url'] = re.sub (r'(?P<cs>[A-Za-z]{3})\d{3}(?!\d+)',
            self._copycase (crscode), req['url'], flags = re.IGNORECASE)

    req['url'] = re.sub (r'(?P<cs>tma)[1-3]', self._copycase(tma), req['url'], flags = re.IGNORECASE)


    for k in req.get(self.dt0, {}):
        req[self.dt0][k] = re.sub (r'(?P<cs>nou)\d{9}', self._copycase (matno), req[self.dt0][k], flags = re.IGNORECASE)

        req[self.dt0][k] = re.sub (r'(?P<cs>[A-Za-z]{3})\d{3}(?!\d+)',
                    self._copycase (crscode), req[self.dt0][k], flags = re.IGNORECASE)

        req[self.dt0][k] = re.sub (r'(?P<cs>tma)[1-3]',
                    self._copycase(tma), req[self.dt0][k], flags = re.IGNORECASE)

    return req

def fetch(qmgr):
    if force or (self.dt1 or self.dt0) not in self.nextq:
        self.fargs.update (url = url1 or self.fargs['url'])

        kwargs.setdefault (
                'headers',
                dogs.mkheader (self.fargs ['url'], self.referer)
                )

        self.qres = self.nav.session.request(**self.fargs , **kwargs)

        self.referer1 = self.qres.url

        self.qres.raise_for_status ()
        self.nextq = dogs.fill_form (
                self.qres.text,
                self.qres.url,
                flags = dogs.FILL_FLG_EXTRAS,
                data = {
                    self.qmap ['ans']: None
                    }
                )

    if not self.dt1:
        self.dt1 = 'data' if self.nextq ['method'] in ('POST', 'post') else 'params'

    return self.nextq.pop (self.dt1)



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

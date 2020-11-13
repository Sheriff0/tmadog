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
import os
import sys
import builtins 
import pathlib

import status

P_PWD = "pwd",
P_USR = "matno";
P_CRSCODE = 'crscode'
P_TMA = 'tma'
P_URL = 'url'
P_WMAP = 'wmap'
P_COOKIES = 'cookies'
P_SESSION = 'session'


class AppendList(argparse.Action):
    def __init__(self,*posargs,**kwargs):
        super().__init__(*posargs, **kwargs);
    def __call__(self, parser, namespace, values, opt_string):
        if not hasattr(namespace, self.dest) or getattr(namespace,
                self.dest) == None:
            setattr(namespace, self.dest, []);
        if isinstance(values, list):
            getattr(namespace, self.dest).extend(values);
        else:
            getattr(namespace, self.dest).append(values)


def is_Challenge_Request(resp):
    return cloudscraper.is_Firewall_Blocked(resp) or
cloudscraper.is_New_Captcha_Challenge(resp) or
cloudscraper.is_New_IUAM_Challenge(resp) or
cloudscraper.is_Captcha_Challenge(resp) or cloudscraper.is_IUAM_Challenge(resp);


import requests_html
import re
from urllib import parse
import lxml
import pdb

requests = requests_html.requests

re.Match = type (re.match (r'foo', 'foo'))

LCLICK = None

class DogTypeError (TypeError):
    def __init__ (self, *pargs, **kwargs):
        super ().__init__ (*pargs, **kwargs)

class FDict (lxml.html.FieldsDict):
    def __init__ (self, form, *a0, **a1):
        self.form_ref = requests_html.HTML (html = form)

        return super ().__init__ (*a0, **a1)

    def __len__ (self):
        return len (dict (self))

    def copy (self):
        return requests.structures.OrderedDict (self)

    def resolve_key (self, s):

        if s.startswith ('['):
            ele = self.form_ref.find (
                    'input[placeholder="%s"]' % (s.strip ('[]'),),
                first = True
                )
            if not ele:
                raise KeyError ('%s does not exist in form' % (s,))

            s = ele.attrs['name']

        elif s.startswith ('<'):
            p_ele = self.form_ref.find (
                    'form *',
                    containing = s.strip ('<>'),
                    first = True
                    )
            if not p_ele:
                raise KeyError ('%s does not exist in form' % (s,))

            ele = p_ele.find ('input', first = True)

            s = ele.attrs['name']

        return s

    def update (self, E, **F):
        if getattr (E, 'keys', None):
            for k in E:
                v = E[k]
                k = self.resolve_key (k)
                self[k] = v
        else:
            for k, v in E:
                k = self.resolve_key (k)
                self[k] = v

        for k in F:
            v = F[k]
            k = self.resolve_key (k)
            self[k] = v

        return self



class AnyheadList:
    def __init__ (self, arr, svalue = None, sidx = None):
        self.garr = (x for x in arr)

        self._arr = {}

        self.sidx = sidx

        if not sidx or svalue == None:
            for i, v in enumerate (self.garr):

                if svalue != None and svalue == v:
                    self.sidx = i
                    break
                elif svalue == None:
                    self.sidx = i
                    svalue = v
                    break

                self._arr ['-' + str (i)] = v

        self.iidx = 0
        self._arr ['-' + str (self.sidx)] = svalue
        self._arr [str (self.iidx)] = svalue

        self.pidx = self.sidx + 1
        self.exhausted = False

    def __repr__ (self):
        strv = '['

        vgen = iter (self)

        try:
            strv += str (next (vgen))
        except StopIteration:
            return '[]'

        for v in vgen:
            strv += ', ' + str (v)

        return strv + ']'

    def __iter__ (self):
        idx = 0

        while True:
            try:
                yield self [idx]

            except IndexError:
                return

            idx += 1

    def __next__ (self):
        yield from self.__iter__ ()

    def origin (self):
        return self.Orderly (self._arr)

    def __setitem__ (self, idx, value):
        self [idx]
        self._arr [str (idx)] = value

    def __getitem__ (self, idx):
        idx = str (idx)
        if not self.exhausted and idx not in self._arr:
            while self.pidx != self.sidx:
                try:
                    self.iidx += 1
                    y = next (self.garr)
                    self._arr [str (self.iidx)] = y
                    self._arr ['-' + str (self.pidx)] = y

                    self.pidx += 1

                    if int (idx) == self.iidx:
                        break

                except StopIteration:
                    self.iidx -= 1
                    self.pidx = 0
                    self.garr = iter (self.Orderly (self._arr))

            if self.pidx == self.sidx:
                self.exhausted = True

        elif self.exhausted and idx not in self._arr:
            raise IndexError (idx)

        return self._arr [idx]

    class Orderly:
        def __init__ (self, dict_arr):
            self.dict_arr = dict_arr

        def __iter__ (self):

            for k in sorted (self.dict_arr.keys ()):
                if re.fullmatch (r'-\d+', k):
                    yield self.dict_arr [k]
                else:
                    return

        def __next__ (self):
            yield from self.__iter__ ()

        def __setitem__ (self, idx, value):
            self.dict_arr ['-' + str (idx)] = value

        def __getitem__ (self, idx):

            return self.dict_arr ['-' + str (idx)]


#__all__ = ['click', 'fill_form', 'getdef_value']

NO_TXTNODE_KEY = 0b0001
NO_TXTNODE_VALUE = 0b0010
FILL_RET_DATAONLY = 0b0100
URLONLY = 0b1000
FILL_FLG_EXTRAS = 0b10000

LastForm = {}

#def fill_radio ():

#def fill_checkbox ():

def fill_form (
        html,
        url = 'https://machine.com/dir/file.ext',
        flags = NO_TXTNODE_VALUE | NO_TXTNODE_KEY,
        selector = 'form',
        idx = 0,
        data = {}
        ):


    s = html

    html = lxml.html.fromstring (html = s, base_url = url)

    tform = html.cssselect (selector)

    if not len (tform):
        raise DogTypeError ('No form found')
    else:
        tform = tform[idx]

    targs = {}

    targs['method'] = tform.method

    targs['url'] = parse.urljoin (tform.base_url, tform.action)

    if flags & URLONLY:
        return targs['url']

    if flags & FILL_FLG_EXTRAS:
        for e in tform.__copy__().cssselect ('form button[name]'):
            tform.append (requests_html.HTML (html = '''<input name = "%s" value = "%s">''' %
                (e.get ('name'), e.get ('value', ''))).find ('input', first = True).element)

    ifields = FDict (lxml.html.tostring (tform, with_tail = False, encoding = 'unicode'), tform.inputs)

    ifields.update (data)

    for k in ifields:

        if ifields[k] is None and not k in data:
            ifields[k] = ''

    targs['data'] = ifields

    if flags & FILL_RET_DATAONLY:
        return targs['data']

    if targs['method'] in ('GET', 'get'):
        targs['params'] = targs.pop ('data')

    return targs


def click (html, url, button, selector = 'a, form', idx = 0, **kwargs):

    global LCLICK

    html = lxml.html.fromstring (html = html, base_url = url)

    x = html.cssselect (selector)

    c = -1

    if idx < 0:
        idx = abs (idx) - 1
        x = reversed (x)

    for m in x:
        if re.match (button.strip (), m.text_content ().strip (), flags = re.I):# or re.search (button.strip (), m.text_content ().strip (), flags = re.I):
            c += 1

        if c == idx:
            LCLICK = m
            break

    if c != idx:
        raise DogTypeError ('No such button %s found' % (button))

    t = m.tag

    if t in ('form', 'FORM'):
        flags = kwargs.pop ('flags', NO_TXTNODE_KEY | NO_TXTNODE_VALUE)
        return fill_form (lxml.html.tostring (m, with_tail = False, encoding = 'unicode'), url, flags = flags, **kwargs)

    elif t in ('a', 'A'):
        flags = kwargs.pop ('flags', ~(URLONLY | FILL_RET_DATAONLY))

        if flags & URLONLY:
            return parse.urljoin (url, m.get('href'))

        elif flags & FILL_RET_DATAONLY:
            return dict (
                    map (
                        lambda a: (parse.unquote_plus (a.split ('=')[0]), parse.unquote_plus (a.split ('=')[-1])),
                        parse.urlparse (parse.urljoin (url, m.get('href'))).query.split ('&')
                        )
                    )

        else:
            return {
                    'method': 'GET',
                    'url': parse.urljoin (url, m.get('href')),
                    }

    else:
        return None

def mkheader (url, ref = None):

    url = parse.urlparse (url)
    ref = parse.urlparse (ref) if ref else None
    headers = {
                'host': url.hostname,
                'origin': '%s://%s' % (url.scheme, url.hostname),
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                }

    if ref:
        headers ['referer'] = ref.geturl ()

    if ref and url.geturl ().split ('/')[0] == ref.geturl ().split ('/')[0]:
        headers ['sec-fetch-site'] = 'same-origin'
    elif ref and url.hostname.endswith (ref.hostname.split ('.', 1)[-1]):
        headers ['sec-fetch-site'] = 'same-site'
    elif not ref:
        headers ['sec-fetch-site'] = 'none'
    else:
        headers ['sec-fetch-site'] = 'cross-site'

    return headers



class LastList:
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

def cookie_hook(nav):
    return nav;

def nav_hook(nav):
    return nav;

def init_hooks(**kwargs):
    global cookie_hook;

    if "cookie_hook" in kwargs:
        cookie_hook = kwargs.pop("cookie_hook");

    if "nav_hook" in kwargs:
        nav_hook = kwargs.pop("nav_hook"); 

def need_cookies(nav, res):
    return re.search(nav.wmap["event"]["on_cookie"], res.text, flags = re.I |
            re.S | re.M) or is_Challenge_Request(res);


def complete(nav, res):
    return re.search(nav.wmap["event"]["on_complete"], res.text, flags = re.I |
            re.S | re.M);


def is_correct_ans(nav, res):
    x = re.search (r"(?P<mark>[01])\s*" + nav.webmap
            ["fb"]["on_qst_submit"].strip (), res.text, re.I);

    if x:
        x = int (x.group ("mark"));
        return x;
    else:
        return status.Status(status.S_ERROR, "no marks found", res);



def logout(nav):
    try:
        nav["logout_page"];
        return nav;

    except BaseException as err:
        return status.Status(status.S_ERROR, "logout err", err);


def login(nav):
    # to make sure we are safe to login. it shouldn't be problematic at all
    # times.
    if "profile_page" in nav or "tma_page" in nav:
        st = logout(nav);

        if not st:
            return st;

    try:
        nav["profile_page"];
        return nav;

    except BaseException as err:
        return status.Status(status.S_ERROR, "login err", err);


## variants with retries
def rlogout(nav, retry = 3):
    retry += 1;
    lreq, fro = nav("logout_page")[:-1];
    while retry:
        try:
            lres = nav.session.request(**lreq , **kwargs);
            lres.raise_for_status();
            nav.cache["logout_page"] = lres;
            # passed here is always sucess - no clean way to confirm a sucessful
            # logout as no page depends on its page
            return nav; 

        except BaseException as err:
            if need_cookies(nav, lres):
                cookie_hook(nav);

            retry -= 1;

    return status.Status(status.S_ERROR, "logout err", lres);


def rlogin(nav, retry = 3):
    if "profile_page" in nav or "tma_page" in nav:
        st = rlogout(nav, retry);

        if not st:
            return st;

    retry += 1;
    
    lreq, fro = nav("profile_page")[:-1];

    while retry:
        try:
            lres = nav.session.request(**lreq , **kwargs)
            lres.raise_for_status();
            nav.cache["profile_page"] = lres;
            ## will raise if not logged-in
            nav("tma_page")[:-1];

            return nav;

        except BaseException as err:
            if need_cookies(nav, lres):
                cookie_hook(nav);

            retry -= 1;

    return status.Status(status.S_ERROR, "login err", lres);


def create_nav(key):
    return navigation.Navigator (
            key[P_URL],
            key[P_WMAP],
            key,
            session = requests.Session ()
            );

def discovercrs (usr, nav):
    ## incase that isn't done already
    reconfigure(nav, usr);
    st = rlogin(nav);
    if not st:
        yield st;
    
    else:
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
                yield m.group (0)

            try:
                rec = iter (navigation.Recipe (path, str (idx), usr, tpage,
                    usr [P_URL]))

                to = next (rec)
            except TypeError:
                break

            idx += 1

def is_arg_valid(cmdl, arg):
    # a usr being in the group of users is the only concrete proof of validity
    if P_USR in cmdl.__dict__ and P_USR in arg:
        return arg[P_USR] in cmdl.__dict__[P_USR];
    else:
        return False;

def is_net_valid_arg(arg):
    # an arg can only go rogue when validated against a network. So, return the
    # only value that can necessitate such a validation in the first place as
    # this is the only place where the result lives.
    return arg[P_CRSCODE];

def preprocess(args):
    global P_URL, P_CRSCODE, P_TMA, P_COOKIES, P_SESSION, P_WMAP, P_USR, P_PWD

        args = args.__dict__;
        matnos = LastList (args ['matno'])
        pwds = LastList (args ['pwd'])
        crscodes = LastList (args ['crscode'])
        tmas = LastList (args ['tma'])
        cookies = LastList (args ['cookies'])
        urls = LastList (args ['url'])
        wmap = configparser.ConfigParser (interpolation =
            configparser.ExtendedInterpolation ())
        wmap.read (args["wmap"]);
        P_USR = wmap ['kmap']['matno']
        P_PWD = wmap ['kmap']['pwd']
        argc = max (len (self.crscodes), len (self.tmas), len (self.matnos))
        usr = {};
        usr [P_WMAP] = wmap;

    for i in range (self.len):

        usr[P_USR] = matnos [i]
        usr[P_PWD] = pwds [i]
        usr[P_TMA] = tmas [i]
        usr[P_URL] = urls [i]

        y = crscodes [i]

        if re.match('all',y, re.I):
            for crs in discovercrs (nav_hook(usr), usr):
                usr[P_CRSCODE] = crs;
                yield usr.copy ();
                if not crs:
                    break;
        else:
            usr[P_CRSCODE] = y;
            yield usr.copy ();


## this for now, is case-insensitive
def get_key_usr(key):
    return key[P_USR].lower();

## others are returned "as is"
def get_key_pwd(key):
    return key[P_PWD];

def get_key_url(key):
    return key[P_URL];

def get_key_course(key):
    return key[P_CRSCODE].lower();

def get_key_tma(key):
    return key[P_TMA];

def get_key_webmap(key):
    return key[WEBMAP];


def reconfigure(nav, usr):
    nav.reconfigure(usr[P_URL], usr[P_WMAP], usr);
    return nav;


def unassign(nav):
    return logout(nav);


def assign(usr, nav = None):
    if nav == None:
        nav = create_nav(usr);
        return (rlogin(nav));
    
    else:
        if self.get_key_usr(self.nav.keys) != get_key_usr(cli):
            # maybe we don't need this
            #unassign(nav);
            return rlogin(reconfigure(nav, usr));
    


def session_from_cookies (url, cookie_file):

    if pathlib.Path(cookie_file).exists():
        with open (cookie_file) as f:
            cookie_str = f.read ();

    else:
        cookie_str = cookie_file;
    
    try:
        cookt = cookie_parse.bake_cookies (cookie_str, url);

    except BaseException as err:
        return status.Status(status.S_ERROR, "cookie error", err);

    if not cookt:
        return status.Status(status.S_ERROR, "no cookies", cookt);

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



fetch_t = dict;
F_QUESTION = "qst";
F_SREQUEST = "request";
F_FREQUEST = "request";
F_QKEY = "data";
F_REFERER = "ref";
F_PSEUDO_ANS = "pseudos"
F_QMAP = "qmap";
F_LAST_FETCH = None;

def copycase (repl):
    def _copycase(m):
        return repl.upper () if m['cs'].isupper () else repl.lower ()

    return _copycase


def mask (qst, mpat, mvalue):
    dic1 = requests.structures.OrderedDict ()
    for k, v in qst.items ():
        if isinstance (v, str):
            v = re.sub (r"(?P<cs>" + mpat + ")",
                    copycase (mvalue), v, flags =
                    re.I);
        dic1 [k] = v;

    return dic1;



def answer_lax(qst, amgr):
    x = copy.deepcopy (qst);

    x = amgr.answer (x);

    if x and x != ansm.ANS_NOANSWER and qst [amgr.qmap["qid"]] == x[amgr.qmap["qid"]]:
        return x;
    else:
        return qst;

def submit(nav, sreq, retry = 3, **kwargs):
    x = 0;
    rt = retry + 1;
    while rt:
        try:
            res = nav.session.request (**sreq, **kwargs);
            res.raise_for_status ();
            
            st = is_correct_ans(nav, res);
            if isinstance(st, int):
                return st;
            


        except BaseException as err:
            if need_cookies(nav, res):
                cookie_hook(nav);

            st = login(nav);
            if not st:
                return status.Status(status.S_ERROR, "submit/login err", (sreq, res, st));

            rt -= 1;

    return status.Status(status.S_ERROR, "submit retries expended", (sreq, res));


def transform_req (req, usr):
    global F_QKEY;
    req = copy.deepcopy(req);
    tma = str (usr[P_TMA]);
    tma = 'tma' + tma if not tma.startswith (('tma', 'Tma', 'TMA')) else tma;
    matno = usr[P_USR];
    crscode = usr[P_CRSCODE];

    F_QKEY = 'data' if req['method'] in ('POST', 'post') else 'params'
    req['url'] = re.sub (r'(?P<cs>nou)\d{9}', copycase (matno), req['url'], flags = re.IGNORECASE)

    req['url'] = re.sub (r'(?P<cs>[A-Za-z]{3})\d{3}(?!\d+)',
            copycase (crscode), req['url'], flags = re.IGNORECASE)

    req['url'] = re.sub (r'(?P<cs>tma)[1-3]', copycase(tma), req['url'], flags = re.IGNORECASE)


    for k in req.get(F_QKEY, {}):
        req[F_QKEY][k] = re.sub (r'(?P<cs>nou)\d{9}', copycase (matno), req[F_QKEY][k], flags = re.IGNORECASE)

        req[F_QKEY][k] = re.sub (r'(?P<cs>[A-Za-z]{3})\d{3}(?!\d+)',
                    copycase (crscode), req[F_QKEY][k], flags = re.IGNORECASE)

        req[F_QKEY][k] = re.sub (r'(?P<cs>tma)[1-3]',
                    copycase(tma), req[F_QKEY][k], flags = re.IGNORECASE)

    return req;



def fetch_all(nav, usr, retry = 3, **kwargs):
    global F_LAST_FETCH;

    to, fro = nav ('qst_page')[:-1];

    freq = transform_req(to, usr);
    
    referer = fro.url;

    pseudos = nav.wmap["qmap"]['pseudo_ans'].split (',');
    
    result = ftype();

    result[F_PSEUDO_ANS] = pseudo_ans.copy();
    result[F_QMAP] = nav.wmap["qmap"];

    done = False;

    while not done:
            kwargs.setdefault (
                    'headers',
                    mkheader (freq['url'], referer)
                    )
            rt = retry + 1;
            while rt:
                try:
                    qres = nav.session.request(**freq , **kwargs)
                    
                    qres.raise_for_status ();

                    result = ftype();

                    result[F_SREQUEST] = fill_form (
                            qres.text,
                            qres.url,
                            flags = FILL_FLG_EXTRAS,
                            data = {
                                nav.wmap["qmap"]['ans']: None
                                }
                            )
                    result[F_QKEY] = result[F_SREQUEST].pop(F_QKEY);

                    referer = qres.url;
                    result[F_REFERER] = referer;
                    F_LAST_FETCH = ftype();
                    F_LAST_FETCH[F_FREQUEST] = copy.deepcopy(qres);
                    F_LAST_FETCH[F_REFERER] = referer;

                    yield copy.deepcopy(result);
                    break;
                

                except BaseException as err:

                    if complete(nav, qres):
                        yield status.Status(status.S_OK, "no more question",
                                qres);
                        done = True;
                        break;

                    elif need_cookies(nav, res):
                        cookie_hook(nav);

                    st = login(nav);
                    if not st:
                        yield status.Status(status.S_ERROR, "submit/login err", (sreq, res, st));

                    rt -= 1;



def fetch_one(nav, usr, retry = 3, **kwargs):
    global F_LAST_FETCH;
    
    if not F_LAST_FETCH:
        f_type = next(fetch_all(nav, usr));
        if F_QUESTION in f_type:
            return f_type[F_QUESTION];
        else:
            return f_type;
    else: 
        freq = F_LAST_FETCH[F_FREQUEST];

    kwargs.setdefault (
            'headers',
            dogs.mkheader (freq ['url'], F_LAST_FETCH[F_REFERER]),
            )

    while retry:
        try:
            res = nav.session.request(**freq , **kwargs);

            res.raise_for_status ()
            return dogs.fill_form (
                    res.text,
                    res.url,
                    flags = dogs.FILL_FLG_EXTRAS,
                    data = {
                        nav.wmap["qmap"]['ans']: None
                        }
                    );
        except BaseException as err:
            if need_cookies(nav, res):
                cookie_hook(nav);

            st = login(nav);
            if not st:
                return status.Status(status.S_ERROR, "submit/login err", (sreq, res, st));

            retry -= 1;



def brute_safe(usr, nav, qst):
    qst1 = fetch_one(usr, nav);
    if qst1:
        return re.match(
                str(qst[nav.wmap["qmap"]["qn"]]),

                str(qst1[nav.wmap["qmap"]["qn"]])
                );
    
    return False;

def brute_submit(usr, nav, f_type, amgr = None, retry = 3, **kwargs):
        
    qst = f_type[F_QKEY].copy() if not amgr else answer_lax(f_type[F_QKEY].copy()i, amgr);
    
    preq = f_type[F_SREQUEST];

    kwargs.setdefault (
            'headers',
            dogs.mkheader (
                f_type[F_SREQUEST]['url'], 
                f_type.get(F_REFERER, "")
                ),
            )

    qst1 = mask (qst, usr[P_USR], kwargs.pop("mask", "Nou123456789"));
    
    x = 0;

    for a in dogs.AnyheadList (f_type[F_PSEUDO_ANS], qst1 [self.qmgr.qmap ["ans"]]):

        qst1 [nav.wmap["qmap"]["ans"]] = a;
        preq[F_QKEY] = qst1;
        
        x = submit(nav, preq);
        if x == 1:
            qst [nav.wmap["qmap"]["ans"]] = a;
            preq[f_type[F_QKEY]] = qst;
            x = submit(nav, preq);

            if x == 0:
                return status.Status(status.S_FATAL, "detected answer is problematic", (preq, qst));
            
            return True;

        elif not brute_safe(usr, nav, qst):
            return status.Status(status.S_FATAL, "unable to brute for the answers from the server", err);
        


def answer_strict(qst, amgr):
    try:
        x = copy.deepcopy (qst);

        x = amgr.answer (x);

        if x and x != ansm.ANS_NOANSWER and qst [qmgr.qmap ["qid"]] == x [qmgr.qmap ["qid"]]:
            return x;

        return errno(qst, amgr);

    except BaseException as err:
        return errno(qst, amgr);;


def addqn(qst, usr, addend = 1):
    qst = qst.copy ();
    n = math.trunc (int (qst [usr[P_WMAP]["qmap"]["qn"]] + "0") / 10) + addend;

    qst [usr[P_WMAP]["qmap"]["qn"]] = str (n);

    return qst;


def addscrore(qst, usr, addend = 1):
    qst = qst.copy ();
    n = math.trunc (int (qst [usr[P_WMAP]["qmap"]["score"]] + "0") / 10) + addend;

    qst [usr[P_WMAP]["qmap"]["score"]] = str (n)

    return qst;


def ch_crscode(qst, usr, crscode = ""):
    out = {};
    for k,v in qst.copy ().items ():
        if isinstance (v, str):
            v = re.sub (r"(?P<cs>" + usr [P_CRSCODE] + ")",
                    copycase (crscode), v, flags =
                    re.I)
        out [k] = v

    return out;

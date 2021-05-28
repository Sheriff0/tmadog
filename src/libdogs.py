#NOTE this library should not be threaded

import math
import re
import requests
import navigation
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
import requests_html
import re
from urllib import parse
import lxml
import pdb
import argparse


import status
import logging
import chardet
import urllib3
import time
import random

CookieClient = None;

copy = copy.copy if sys.implementation.version.minor < 7 else copy.deepcopy 

logger = logging.getLogger('tmadog.libdog');

MAX_RETRIES = 5;
MAX_DELAYS = 3;

P_PWD = "pwd";
P_USR = "matno";
P_PWD_OLD = P_PWD;
P_USR_OLD = P_USR;
P_CRSCODE = 'crscode'
P_TMA = 'tma'
P_URL = 'url'
P_WMAP = 'wmap'
P_COOKIES = 'cookies'
P_SESSION = 'session'

CACHE_PAGE_CACHE = "";
CACHE_OVERWRITE = True;
CACHE_CACHE_FIRST = False;

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



class DogCmdParser(argparse.ArgumentParser):

    def convert_arg_line_to_args(self, arg_line):
        return arg_line.split() if not re.match(r'^\s*#.*', arg_line) else [];


def is_Challenge_Request(resp):
    return cloudscraper.CloudScraper.is_Firewall_Blocked(resp) or cloudscraper.CloudScraper.is_New_Captcha_Challenge(resp) or cloudscraper.CloudScraper.is_New_IUAM_Challenge(resp) or cloudscraper.CloudScraper.is_Captcha_Challenge(resp) or cloudscraper.CloudScraper.is_IUAM_Challenge(resp);

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

            except KeyError: #NOTE: hacky and unsustainable
                return;

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


def collapse_gen(*pargs):
    if not pargs:
        return;
    for gen in pargs:
        for it in gen:
            yield it;

def anyhead_gen(itr, v, idx = None):
    back = [];
    itr = iter(itr);

    for i,it in enumerate(itr):
        back.append(it);
        if not idx:
            if it == v:
                idx = i;
                break;
        elif i == idx:
            break;



    first = back.pop();

    for it in collapse_gen([first], itr, back):
        yield it;

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

    try:
        ifields.update (data);
    except KeyError as err:
        raise DogTypeError ("Form and fill data don't match", err)

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

    s = html

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
    return None;

def nav_hook(nav):
    return None;

def unknown_err_handler_hook(err, *pargs):
    res = input("\n\n%s occured while running.\npress s<enter key> to skip the action, c<enter key> to continue, q<enter key> to quit the program\n" % (err, ));

    if re.match(r's.*', res, re.I):
        return status.Status(status.S_NULL, "skip action", err);
    elif re.match(r'c.*', res, re.I):
        return status.Status(status.S_OK, "continue action", err);
    else:
        raise KeyboardInterrupt();


def init_hooks(**kwargs):
    global cookie_hook, nav_hook, unknown_err_handler_hook, logger;

    logger.debug("initializing requested hooks");

    if "cookie_hook" in kwargs:
        cookie_hook = kwargs.pop("cookie_hook");

    if "nav_hook" in kwargs:
        nav_hook = kwargs.pop("nav_hook");

    if "err_hook" in kwargs:
        unknown_err_handler_hook = kwargs.pop("err_hook");

    if "logger_hook" in kwargs:
        logger = kwargs.pop("logger_hook");

    if "cookie_client" in kwargs:
        CookieClient = kwargs.pop("cookie_client");

    logger.debug("done..");

def need_cookies(nav, res):
    m = False;
    if nav:
        m = re.search(nav.webmap["events"]["on_cookie"], res.text, flags = re.I |
                re.S | re.M);
    
    m = is_Challenge_Request(res) if not m else m;

    if m:
        logger.debug("cookie needed\n=======\nmessage\n=======\n%s\n========\n\n",
                res.text[m.start():]);
    else:
        logger.debug("no cookie needed");

    return m;


def complete(nav, res):
    m = re.search(nav.webmap["events"]["on_complete"], res.text, flags = re.I |
            re.S | re.M);
    if m:
        logger.debug("quiz completed\n=======\nmessage\n=======\n%s\n========\n\n",
                res.text[m.start():]);
    else:
        logger.debug("quiz uncompleted");

    return m;



def is_correct_ans(nav, res):
    text = lxml.html.fromstring(html = res.text).text_content();

    m = re.search (r"(?P<mark>[01])\s*" + nav.webmap
            ["events"]["on_qst_submit"].strip (), text, re.I | re.M | re.DOTALL);


    if m:
        x = int (m.group ("mark"));
        if x:
            logger.debug("bravo!! correct answer\n=======\nmessage\n=======\n%s\n========\n\n",
                text[m.start():]);
        else:
            logger.debug("oops!! wrong answer\n=======\nmessage\n=======\n%s\n========\n\n",
                text[m.start():]);

        return x;
    else:
        logger.debug("oops!! no mark found\n=======\nmessage\n=======\n%s\n========\n\n",
            text);
        return status.Status(status.S_ERROR, "no marks found", res);



def logout(nav):
    try:
        goto_page(nav, "logout_page");
        logger.info("logout(): logged user %s out", nav.keys[P_USR]);
        return nav;

    except BaseException as err: #NOTE replace this catch
        logger.info("logout(): unable to log user %s out due to unknown error %s",
                nav.keys[P_USR], err);
        return status.Status(status.S_ERROR, "logout err", err);


def login(nav):

    try:
        # for compatibility with testing dogrc's
        goto_page(nav, "tma_page");
        logger.info("login(): successfully logged in user %s", nav.keys[P_USR]);
        return nav;

    except BaseException as err: #NOTE replace this catch
        logger.info("login(): can't log user %s in", nav.keys[P_USR]);
        return status.Status(status.S_ERROR, "login err", err);


# very conservative variants with optional retries
def rlogout(nav, retry = 3, **kwargs):
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
                # running-out of cookies is technically a successful
                # logout (atleast for our current target);
                return nav;

            retry -= 1;

    return status.Status(status.S_ERROR, "logout err", lres);


def rlogin(nav, retry = 3, **kwargs):
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
            ## will raise if not logged-in
            nav("tma_page")[:-1];
            nav.cache["profile_page"] = lres;
            return nav;

        except BaseException as err:
            if need_cookies(nav, lres):
                cookie_hook(nav);

            retry -= 1;

    return status.Status(status.S_ERROR, "login err", lres);


def lazy_logout(nav, retry = 3, **kwargs):
    # lazy-easy

    return lazy_nav_reconf(nav, nav.keys);


def is_incorrect_login(nav, qres):
    if not isinstance(qres, requests.Response):
        qres = nav.session.get(nav.keys[P_URL]);

    for tr in nav.webmap["events"]["on_incorrect_login"].strip().split(","):
        mt = re.search(
                tr.strip(),
                lxml.html.fromstring(html = qres.text).text_content(),
                re.I | re.M | re.DOTALL
                );
        if mt:
            logger.debug("it's incorrect login, please handle");
            return mt;

    logger.debug("No incorrect login detected found");
    return False;



def lazy_login(nav, retry = MAX_RETRIES, **kwargs):
    global LOGIN_BLACKLIST;

    retry += 1;
    err_log_fmt = "==LOGIN===\n%s\n=====";

    logger.info("lazy_login(): preparing to login %s", nav.keys[P_USR]);

    lres = False;

    while True:
        try:
            lreq, fro = nav("profile_page")[:-1];
            referer = fro.url;

            kwargs.setdefault (
                    'headers',
                    mkheader (lreq['url'], referer)
                    )

            lres = nav.session.request(**lreq , **kwargs)
            lres.raise_for_status();
            ## will raise if not logged-in
            nav.cache["profile_page"] = lres;
            # to be sure we're truly logged-in
            nav("qst_page")[:-2];
            nav("logout_page")[:-1];

            logger.info("lazy_login(): sucessfully logged-in %s", nav.keys[P_USR]);
            return nav;

        except (DogTypeError, requests.HTTPError) as err:
            logger.info("lazy_login(): loggin unsucessful for %s due to %s",
                    nav.keys[P_USR], err);

            if not isinstance(lres, requests.Response):
                lres = nav.session.get(nav.keys[P_URL]);

            if isinstance(err, DogTypeError) and is_incorrect_login(nav, lres):
                LOGIN_BLACKLIST.append(nav.keys);
                logger.debug(err_log_fmt % (lres.text,));
                return status.Status(status.S_ERROR, "cant' login %s" %
                        (nav.keys[P_USR],), nav.keys);

            elif need_cookies(nav, lres):
                st = cookie_hook(nav);
                if not st:
                    logger.debug(err_log_fmt % (lres.text,));
                    return status.Status(status.S_ERROR, "can't login, no cookies in navigator", lres);

            logger.info("retrying");
            logger.debug("==LOGIN==\n%s\n==========" % (lres.text,));

            time.sleep(random.random() * MAX_DELAYS);


        except requests.RequestException as err:
            if isinstance(err, (
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout
                )) and not isinstance(err.args[0], urllib3.exceptions.MaxRetryError):
                logger.debug("retrying..." if retry > 1 else "exiting...");

                retry -= 1;

            elif unknown_err_handler_hook(err):
                retry -= 1;
            else:
                logger.info("lazy_login(): loggin unsucessful for %s due to %s, suspending",
                        nav.keys[P_USR], err);

                return status.Status(status.S_ERROR, "can't login, unknown err", (lres, err));

    return status.Status(status.S_ERROR, "can't login, maximum retries exceeded", lres);



def goto_page(nav, pg, stp = None, retry = MAX_RETRIES, login = False):
    retry += 1;
    
    logger.debug("goto_page(): preparing navigate to %s", pg);

    lres = None;

    while retry:
        try:
            lres = nav(pg)[:stp];

            logger.debug("goto_page(): sucessfully navigated to %s", pg);
            return lres;

        except Exception as err:
            logger.debug("goto_page(): navigation unsucessful for %s due to %s, " , pg, err);

            if isinstance(err, (DogTypeError, requests.HTTPError)):

                if not can_retry_page(nav, lres, login):
                    logger.debug("exiting...");
                    return status.Status(status.S_ERROR, "can't goto %s" % (pg,), lres);

                logger.debug("retrying..." if retry > 1 else "exiting...");

                retry -= 1;

            elif isinstance(err, (
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout
                )) and not isinstance(err.args[0], urllib3.exceptions.MaxRetryError):
                logger.debug("retrying..." if retry > 1 else "exiting...");

                retry -= 1;

            elif isinstance(err, requests.exceptions.RequestException):
                if not unknown_err_handler_hook(err, lres):
                    logger.debug("halting...");
                    return status.Status(status.S_ERROR, "unknown err while navigating to %s" % (pg,), (lres, err));


                logger.debug("retrying..." if retry > 1 else "exiting...");

                retry -= 1;

            else:
                raise err;


    return status.Status(status.S_ERROR, "maximum retries exceeded for navigation to %s" % (pg,), lres);



def goto_page2(nav, req, retry = MAX_RETRIES, login = False, **kwargs):
    retry += 1;
    
    logger.debug("goto_page2(): preparing to send to server");

    lres = None;

    while retry:
        try:
            lres = nav.session.request(**req, **kwargs);
            lres.raise_for_status();

            logger.debug("goto_page2(): sucessfully sent to server");
            return lres;

        except Exception as err:
            logger.debug("goto_page2(): sending unsucessful due to %s" , err);

            if isinstance(err, (DogTypeError, requests.HTTPError)):

                if not can_retry_page(nav, lres, login):
                    logger.debug("exiting...");
                    return status.Status(status.S_ERROR, "can't send to server", lres);

                logger.debug("retrying..." if retry > 1 else "exiting...");

                retry -= 1;

            elif isinstance(err, (
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout
                )) and not isinstance(err.args[0], urllib3.exceptions.MaxRetryError):
                logger.debug("retrying..." if retry > 1 else "exiting...");

                retry -= 1;

            elif isinstance(err, requests.exceptions.RequestException):
                if not unknown_err_handler_hook(err, lres):
                    logger.debug("halting...");
                    return status.Status(status.S_ERROR, "unknown err while sending to server", (lres, err));


                logger.debug("retrying..." if retry > 1 else "exiting...");

                retry -= 1;

            else:
                raise err;


    return status.Status(status.S_ERROR, "maximum retries exceeded for sending to server", lres);



def create_nav(key):
    return navigation.Navigator (
            key[P_URL],
            key[P_WMAP],
            key,
            session = requests.Session ()
            );

def discovercrs (usr, nav, retry = 3):
    crs = None;

    # only one loop is used - the first where one or more courses was found.
    # no checks for duplicate courses yet, like a hack to repeat a submission on
    # mostly, cookies expiring.

    #for crs in discover_by_crslist(usr, nav, retry):
    #    yield crs;

    yield from discover_by_quizlist(usr, nav, retry);

def discover_by_quizlist(usr, nav, retry = 3):
    global F_QFMT;

    st = assign(usr, nav);
    if not st:
        logger.info("discovery mode setup failed for %s.. skipping", usr[P_USR]);
        yield st;

    else:

        retry += 1

        lg = lazy_login(nav);

        if not lg:
            yield lg;
            return;

        st = goto_page(nav, "qst_page", -1, login = True);

        if not st:
            yield st;
            return;

        to, tpage = st;
        idx = int (nav.webmap ['qst_page']['indices'].split (',')[-1])
        path = nav.webmap ['qst_page']['path'].split (',')[-1]


        idx += 1

        while True: #crscode discovery
            dt = 'data' if to ['method'] in ('POST', 'post') else 'params'

            m = None

            for k in to.get (dt, {}).values ():
                m = re.search (usr[P_WMAP]["describe"]["crscode"], k)

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

def discover_by_crslist(usr, nav, retry = 3):

    st = assign(usr, nav);
    if not st:
        logger.info("discovery mode setup failed for %s.. skipping", usr[P_USR]);
        yield st;

    else:
        logger.info("trying to discover courses for %s",
                    nav.keys[P_USR]);

        st = goto_page(nav, "quiz_list", login = True, retry = retry);

        for m in re.finditer(usr[P_WMAP]["describe"]["crscode"], st.text, re.I):

            logger.info("found %s", m.group(0));
            yield m.group (0)


TMANO_STRICT = 0;
TMANO_LAX = 1;

def get_valid_qreq(usr, nav):
    st = goto_page(nav, "qst_page", -1, login = True);

    if not st:
        return st;

    to, tpage = st;
    idx = int (nav.webmap ['qst_page']['indices'].split (',')[-1])
    path = nav.webmap ['qst_page']['path'].split (',')[-1]


    idx += 1

    while True: #crscode discovery
        dt = 'data' if to ['method'] in ('POST', 'post') else 'params'

        has_mat = False;
        has_crs = False;
        has_tma = False;
        for k in to.get (dt, {}).values ():
            if not has_crs:
                has_crs = re.search (nav.webmap["describe"]["crscode"], k);

            if not has_tma:
                has_tma = re.search (nav.webmap["describe"]["tma"], k, re.I);

            if not has_mat:
                has_mat = re.search (nav.webmap["describe"]["matno"], k, re.I);

            if has_mat and has_crs and has_tma:
                return (to, tpage);

        try:
            rec = iter (navigation.Recipe (path, str (idx), usr, tpage,
                usr [P_URL]))

            to = next (rec)
        except TypeError:
            break

        idx += 1

    return status.Status(status.S_NULL, "no valid question request", cause = tpage);


def is_arg_valid(cmdl, arg):
    # a usr being in the group of users is the only concrete proof of validity
    if (P_USR in cmdl.__dict__ and P_USR in arg):
        return arg[P_USR] in cmdl.__dict__[P_USR];

    elif P_USR_OLD in cmdl.__dict__ and P_USR_OLD in arg:
        return arg[P_USR_OLD] in cmdl.__dict__[P_USR_OLD];

    elif P_USR_OLD in cmdl.__dict__ and P_USR in arg:
        return arg[P_USR] in cmdl.__dict__[P_USR_OLD];
    else:
        return False;

def is_net_valid_arg(cmdl, arg):
    # an arg can only go rogue when validated against a network. So, return the
    # only value that can necessitate such a validation in the first place as
    # this is the only place where the result lives.
    return is_arg_valid(cmdl, arg) and arg[P_CRSCODE];

LOGIN_BLACKLIST = [];

def preprocess(args, excl_crs = [], whitelist = None, max_wlist = None, wlist_cb
        = None, *pargs, **kwargs):
    global P_URL, P_CRSCODE, P_TMA, P_COOKIES, P_SESSION, P_WMAP, P_USR, P_PWD;
    global LOGIN_BLACKLIST;
    
    if not excl_crs:
        excl_crs = [];

    args = args.__dict__;
    matnos = LastList (args [P_USR_OLD]);
    pwds = LastList (args [P_PWD_OLD]);
    crscodes = LastList (args [P_CRSCODE]);
    tmas = LastList (args [P_TMA]);
    urls = LastList (args [P_URL]);
    wmap = args["wmap"];
    P_USR = wmap ['kmap']['usr']
    P_PWD = wmap ['kmap']['pwd']
    argc = max (len (crscodes), len (tmas), len (matnos))

    for i in range (argc):
        usr = {};
        if whitelist != None and max_wlist:
            wlen = len(whitelist);
            if wlen >= max_wlist and matnos [i] not in whitelist:
                logger.info("skipping %s: maximum user list has been reached", matnos [i]);
                continue;

            elif wlen < max_wlist and matnos [i] not in whitelist:
                whitelist.append(matnos [i]);
                if not wlist_cb(whitelist):
                    logger.info("There is a problem with the whitelist handler");
                    return None;

        usr[P_WMAP] = wmap;
        usr[P_USR] = matnos [i]
        usr[P_PWD] = pwds [i]
        usr[P_TMA] = tmas [i]
        usr[P_URL] = urls [i]

        y = crscodes [i]

        if re.match('all', y, re.I):
            logger.info("preprocess(): no course specified for user %s, entering course discovery mode",
                    usr[P_USR]);

            for crs in discover_by_quizlist (usr, nav_hook(usr)):
                if crs:
                    mt = None;
                    for x_crs in excl_crs:
                        mt = re.match(x_crs,  crs, re.I);
                        if mt:
                            break;

                    if mt:
                        logger.info("skipping %s" % (crs,));
                        continue;

                yy = copy(usr);

                if not isinstance(crs, status.Status):
                    logger.info("found %s for user number %s of %s", crs, i+1,
                            argc);
                    yy[P_CRSCODE] = crs;
                    yield yy;
                else:
                    LOGIN_BLACKLIST.append(yy);
                    yy.pop(P_CRSCODE, None);
                    yield status.Status(status.S_ERROR, "can't login", cause =
                            yy);
                    break;
        else:
            logger.info("%s specified for user number %s of %s", y, i+1, argc);
            usr[P_CRSCODE] = y;
            yield copy(usr);


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

def lazy_nav_reconf(nav, usr):
    nv = navigation.Navigator(usr[P_URL], usr[P_WMAP], usr, session = nav.session, **nav.kwargs);
    if nav.keys[P_URL] == usr[P_URL] and "home_page" in nav:
        nv.cache["home_page"] = nav.cache["home_page"];
    return nv;

def reconfigure(nav, usr):
    nav.reconfigure(usr[P_URL], usr[P_WMAP], usr);
    return nav;


def unassign(nav):
    return lazy_logout(nav);


def assign(usr, nav = None):
    if not nav:
        nav = create_nav(usr);
        return nav;

    elif re.match(nav.keys[P_USR], usr[P_USR], re.I):
        # maybe we don't need this
        #unassign(nav);
        return nav;
    else:
        return lazy_nav_reconf(nav, usr);


def read_file_text(fi):
    fi = pathlib.Path(fi);
    if not fi.exists():
        return None;

    fbin = fi.read_bytes();

    enc = chardet.detect(fbin);

    if not enc or not enc["encoding"]:
        logger.info("cannot read file!!!");
        return status.Status(status.S_ERROR, "no text", (enc,));
    
    return fbin.decode(encoding = enc["encoding"]);

import user_agents
import email

ua_gen = iter(user_agents.UA_Header_Generator());

def session_from_cookies (url, cookie_file, cookie_client = None, nav = None):
    # use a unique string else 'fi' defaults to the current dir which always
    # exists.

    fi = pathlib.Path(cookie_file if cookie_file else str(time.time()));

    if fi.exists():
        logger.info("reading cookie file %s" % (cookie_file,));
        cookie_str = read_file_text(cookie_file);
        if not cookie_str:
            return cookie_str;
        

    else:
        cookie_str = str(cookie_file);

    oheaders = [
            "User-Agent",
            "Accept",
            "Accept-Language",
            "Connection",
            "Upgrade-Insecure-Requests",
            ];  

    session = requests.Session ();

    cookt = cookie_parse.bake_cookies (cookie_str, url, others = oheaders);

    if not cookt:
        logger.info("no cookies found...");
        theaders = next(ua_gen);
        tsession = requests.Session();
        tsession.headers = theaders;

        res = just_goto_page(tsession, method = "GET", url = url);
        
        if not need_cookies(nav, res):
            session.cookies = tsession.cookies;

        elif cookie_client:
            #must not fail, atleast for now.
            logger.info("found a cookie client. begin polling a cookie server");
            res = just_goto_page(method = "GET", url = url);
            hdrs = {};
            if isinstance (res, requests.Response) and "Accept-Encoding" in res.request.headers:
                # input headers mush be lower-cased
                hdrs["accept-encoding"] = res.request.headers["Accept-Encoding"];
                oheaders.append("Accept-Encoding");

            dt = cookie_client.push({
                "url": url,
                "headers": hdrs,
                }).wait_set();
            session.cookies = dt.get("cookies");
            theaders = dt.get("headers");

    else:
        logger.info("got cookies created by %s", cookt [0]['User-Agent']);
        theaders = cookt[0];

        session.cookies = cookt [1]
        
    session.headers = requests.structures.OrderedDict();
    sheaders = email.message.Message();

    for k in theaders:
        sheaders[k] = theaders[k];

    for hdr in oheaders:
        if hdr in sheaders:
            session.headers[hdr] = sheaders[hdr];
        else:
            #omit the header altogether
            session.headers[hdr] = None;


    return session



fetch_t = dict;
F_QFMT = None;
F_QUESTION = "qst";
F_SREQUEST = "request";
F_FREQUEST = "request";
F_QKEY = "data";
F_REFERER = "ref";
F_PSEUDO_ANS = "pseudos"
F_QMAP = "qmap";
F_LAST_FETCH = None;
F_NEXT = fetch_t();
F_ENCODING = "encoding";

def copycase (repl):
    srepl = str(repl);

    def _copycase(m):
        try: 
            return srepl.upper () if m['cs'].isupper() else srepl.lower ();
        except IndexError:
            return srepl;

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
    x = copy (qst);

    qst = amgr.answer (qst);

    logger.info("answer_lax(): checking for answer to question in cache");

    if qst and qst != ansm.ANS_NOANSWER and qst [amgr.qmap["qid"]] == x[amgr.qmap["qid"]]:
        logger.info("answer_lax(): answer found in local cache");
        return qst;
    else:
        logger.info("answer_lax(): no answer found in local cache");
        return x;


SUBMIT_QUIZ_SUSPEND = -2;
SUBMIT_RETRY_FETCH = -1;

def submit(nav, sreq, retry = 2, **kwargs):
    logger.info("libdog.submit(): preparing to submit quiz");
    res = None;
    retry += 1
    while retry:
        retry -= 1;

        res = goto_page2(nav = nav, req = sreq, login = True, **kwargs);
        
        if isinstance (res, requests.Response):
            xt = is_correct_ans(nav, res);
            logger.info("libdogs.submit(): submit sucessful, checking result...");

            if not isinstance(xt, status.Status):
                logger.info("libdogs.submit(): checking result successful");

                return xt;
            
            elif is_suspendable(nav, res):
                return status.Status(status.S_INT, "it is suspendable", cause = SUBMIT_QUIZ_SUSPEND);

        if retry:
            logger.info(
                    "libdogs.submit(): checking result failed, retrying..."
                    );
        time.sleep(random.random() * MAX_DELAYS);

    logger.info(
            "libdogs.submit(): checking result failed, retry fetch..."
            );

    return SUBMIT_RETRY_FETCH;



def transform_req (req, usr):
    global F_QKEY;
    req = copy(req);
    tma = str (usr[P_TMA]);
    matno = usr[P_USR];
    crscode = usr[P_CRSCODE];

    F_QKEY = 'data' if req['method'] in ('POST', 'post') else 'params'
    req['url'] = re.sub (usr[P_WMAP]["describe"]["matno"], copycase (matno), req['url'], flags = re.IGNORECASE)

    req['url'] = re.sub (usr[P_WMAP]["describe"]["crscode"],
            copycase (crscode), req['url'], flags = re.IGNORECASE)

    req['url'] = re.sub (usr[P_WMAP]["describe"]["tma"], copycase(tma), req['url'], flags = re.IGNORECASE)


    for k in req.get(F_QKEY, {}):
        req[F_QKEY][k] = re.sub (usr[P_WMAP]["describe"]["matno"], copycase (matno), req[F_QKEY][k], flags = re.IGNORECASE)

        req[F_QKEY][k] = re.sub (usr[P_WMAP]["describe"]["crscode"],
                    copycase (crscode), req[F_QKEY][k], flags = re.IGNORECASE)

        req[F_QKEY][k] = re.sub (usr[P_WMAP]["describe"]["tma"],
                    copycase(tma), req[F_QKEY][k], flags = re.IGNORECASE)

    return req;



def is_skippable(nav, usr, qres):
    if not isinstance(qres, requests.Response):
        qres = nav.session.get(nav.keys[P_URL]);

    if usr:
        for tr in nav.webmap["events"]["crs_skip"].strip().split(","):
            mt = re.match(tr.strip(), usr[P_CRSCODE], re.I);
            if mt:
                logger.debug("you can skip please...");
                return mt;

    for tr in nav.webmap["events"]["page_skip"].strip().split(","):
        mt = re.search(
                tr.strip(),
                lxml.html.fromstring(html = qres.text).text_content(),
                re.I | re.M | re.DOTALL
                );
        if mt:
            logger.debug("you can skip please...");
            return mt;

    logger.debug("no skippables found...");
    return False;


def is_suspendable(nav, qres):
    if not isinstance(qres, requests.Response):
        qres = nav.session.get(nav.keys[P_URL]);

    for tr in nav.webmap["events"]["suspendables"].strip().split(","):
        mt = re.search(
                tr.strip(),
                lxml.html.fromstring(html = qres.text).text_content(),
                re.I | re.M | re.DOTALL
                );
        if mt:
            logger.debug("suspendable found, please handle");
            return mt;

    logger.debug("No suspendable found");
    return False;


def is_trap(nav, qres):
    if not isinstance(qres, requests.Response):
        qres = nav.session.get(nav.keys[P_URL]);

    for tr in nav.webmap["events"]["traps"].strip().split(","):
        mt = re.search(
                tr.strip(),
                lxml.html.fromstring(html = qres.text).text_content(),
                re.I | re.M | re.DOTALL
                );
        if mt:
            logger.debug("it's a trap, please handle");
            return mt;

    logger.debug("No traps found");
    return False;


def can_retry_page(nav, qres, logi = False):
    if not isinstance(qres, requests.Response):
        qres = nav.session.get(nav.keys[P_URL]);

    if need_cookies(nav, qres):
        st = cookie_hook(nav);

        if not st:
            return status.Status(status.S_ERROR, "no cookie in navigator",
                    (qres.request, qres, st));
        if logi:
            st = lazy_logout(st);
            st = lazy_login(st);
            if st:
                return status.Status(status.S_OK, "can retry",
                        qres);

        return status.Status(status.S_ERROR, "login err",
                        (qres.request, qres, st));

    elif login_needed(nav, qres):
        if logi:
            st = lazy_logout(nav);
            st = lazy_login(st);
            if st:
                return status.Status(status.S_OK, "can retry",
                        qres);

        return status.Status(status.S_ERROR, "login err",
                        (qres.request, qres, st));

    
    elif is_trap(nav, qres):
        return status.Status(status.S_OK, "can retry", qres);

    else:
        return status.Status(status.S_ERROR, "can't retry",
                    (qres.request, qres));



def login_needed(nav, qres):
    if not isinstance(qres, requests.Response):
        qres = nav.session.get(nav.keys[P_URL]);

    return re.search(
            nav.webmap["events"]["on_login_needed"].strip(),
            lxml.html.fromstring(html = qres.text).text_content(),
            re.I | re.M | re.DOTALL
            );

def can_retry_fetch(nav, qres, usr):
    if not isinstance(qres, requests.Response):
        qres = nav.session.get(nav.keys[P_URL]);

    if need_cookies(nav, qres):
        st = cookie_hook(nav);

        if not st:
            return status.Status(status.S_ERROR, "no cookie in navigator",
                    (qres.request, qres, st));
        return status.Status(status.S_OK, "can retry",
                qres);


        st = lazy_logout(st);
        st = lazy_login(st);
        if not st:
            return status.Status(status.S_ERROR, "login err",
                    (qres.request, qres, st));

        return status.Status(status.S_OK, "can retry",
                qres);

    elif complete(nav, qres):
        return status.Status(status.S_NULL, "no more question",
                qres);

    elif login_needed(nav, qres):
        st = lazy_logout(nav)
        st = lazy_login(st);
        if not st:
            return status.Status(status.S_ERROR, "submit/login err",
                    (qres.request, qres, st));

        return status.Status(status.S_OK, "can retry",
                qres);

    elif is_trap(nav, qres):
        return status.Status(status.S_OK, "can retry", qres);

    else:
        return status.Status(status.S_ERROR, "can't retry",
                        (qres.request, qres));


def fetch_all(nav, usr, **kwargs):
    global F_LAST_FETCH, F_QFMT, F_NEXT;
    #find an alt
    #if not F_QFMT:
    if CACHE_CACHE_FIRST:
        g = cache_get("qst_page", -1);

        if not g:
            g = get_valid_qreq(usr, nav);
            if g:
                cache_put(g, "qst_page", -1);

    else:
        g = get_valid_qreq(usr, nav);

    if not g:
        yield status.Status(status.S_ERROR, "cannot proceed with the fetch", cause = g);
        return;

    to, fro = g;

    freq = transform_req(to, usr);

    referer = fro.url;

    logger.info("fetch_all(): preparing to fetch all %s questions for %s" %
            (usr[P_CRSCODE], usr[P_USR]));

    pseudos = nav.webmap["qmap"]['pseudo_ans'].split (',');

    result = fetch_t();

    result[F_PSEUDO_ANS] = pseudos.copy();
    result[F_QMAP] = nav.webmap["qmap"];

    done = False;

    while not done:

        kwargs.setdefault (
                'headers',
                mkheader (freq['url'], referer)
                );
        qres = goto_page2(nav, freq ,login = True,  **kwargs);
        if not qres:
            logger.info("fetch_all(): fetch unsucessful, retrying");
            continue;

        try:
            result[F_SREQUEST] = fill_form (
                    qres.text,
                    qres.url,
                    flags = FILL_FLG_EXTRAS,
                    data = {
                        nav.webmap["qmap"]['ans']: None
                        }
                    )

            result[F_QKEY] = result[F_SREQUEST].pop(F_QKEY);

            result[F_ENCODING] = qres.encoding;

            logger.info(
                    "fetch_all(): successful fetched question %s for %s in %s",
                    result[F_QKEY][nav.webmap["qmap"]["qn"]],
                    usr[P_USR],
                    usr[P_CRSCODE]
                    );


            referer = qres.url;
            result[F_REFERER] = referer;
            F_LAST_FETCH = fetch_t();
            F_LAST_FETCH[F_FREQUEST] = copy(freq);
            F_LAST_FETCH[F_REFERER] = referer;

            yield copy(result);

        except DogTypeError as err:
            logger.info("fetch_all(): fetch unsucessful");

            st = can_retry_fetch(nav, qres, usr);
            if st.code == status.S_NULL:
                logger.info("nothing to fetch");
                done = True;
                yield st;

            elif is_skippable(nav, usr, qres):
                logger.info("nothing to fetch");
                done = True;
                yield status.Status(status.S_ERROR, "can be skipped",
                        qres);

            elif is_suspendable(nav, qres):
                done = True;
                yield status.Status(status.S_INT, "it is suspendable", cause = SUBMIT_QUIZ_SUSPEND);

            else:
                logger.info("fetch_all(): retrying fetch");
                time.sleep(random.random() * MAX_DELAYS);
            



def fetch_allq(nav, usr, **kwargs):
    global F_LAST_FETCH, F_QFMT, F_NEXT;

    #find an alt
    #if not F_QFMT:
    if CACHE_CACHE_FIRST:
        g = cache_get("qst_page", -1);

        if not g:
            g = get_valid_qreq(usr, nav);
            if g:
                cache_put(g, "qst_page", -1);

    else:
        g = get_valid_qreq(usr, nav);

    if not g:
        yield status.Status(status.S_ERROR, "cannot proceed with the fetch", cause = g);
        return;

    to, fro = g;

    freq = transform_req(to, usr);

    referer = fro.url;

    pseudos = nav.webmap["qmap"]['pseudo_ans'].split (',');

    result = fetch_t();

    result[F_PSEUDO_ANS] = pseudos.copy();
    result[F_QMAP] = nav.webmap["qmap"];

    done = False;

    while not done:

        kwargs['headers'] = mkheader (freq['url'], referer);

        qres = goto_page2(nav, freq ,login = True,  **kwargs);
        if not qres:
            continue;

        try:
            result[F_SREQUEST] = fill_form (
                    qres.text,
                    qres.url,
                    flags = FILL_FLG_EXTRAS,
                    data = {
                        nav.webmap["qmap"]['ans']: None
                        }
                    )

            result[F_QKEY] = result[F_SREQUEST].pop(F_QKEY);
            result[F_ENCODING] = qres.encoding;


            referer = qres.url;
            result[F_REFERER] = referer;
            F_LAST_FETCH = fetch_t();
            F_LAST_FETCH[F_FREQUEST] = copy(freq);
            F_LAST_FETCH[F_REFERER] = referer;

            yield copy(result);

        except DogTypeError as err:
            st = can_retry_fetch(nav, qres, usr);
            if st.code == status.S_NULL:
                logger.info("nothing to fetch");
                done = True;
                yield st;

            elif is_skippable(nav, usr, qres):
                logger.info("nothing to fetch");
                done = True;
                yield status.Status(status.S_ERROR, "can be skipped",
                        qres);


            elif is_suspendable(nav, qres):
                done = True;
                yield status.Status(status.S_INT, "it is suspendable", cause = SUBMIT_QUIZ_SUSPEND);


            else:
                logger.info("fetch_all(): retrying fetch");
                time.sleep(random.random() * MAX_DELAYS);
        
            


def brute_safe(nav, usr, qst, **kwargs):
    global F_NEXT;

    fe = next(iter(fetch_allq(nav, usr, **kwargs)));

    if isinstance(fe, status.Status) and re.search(r'no\s+more\s+question',
            fe.msg, re.I):
        return True;

    elif fe:
        return re.match(
                str(qst[nav.webmap["qmap"]["qn"]]),

                str(fe[F_QKEY][nav.webmap["qmap"]["qn"]])
                );

    return False;


def brute_submit(usr, nav, f_type, amgr = None, retry = 3, fp = None, **kwargs):

    qst = f_type[F_QKEY].copy() if not amgr else answer_lax(f_type[F_QKEY], amgr);

    preq = f_type[F_SREQUEST];

    kwargs.setdefault (
            'headers',
            mkheader (
                f_type[F_SREQUEST]['url'],
                f_type.get(F_REFERER, "")
                ),
            )

    qst1 = mask (qst, usr[P_USR], kwargs.pop("mask", "Nou123456789"));

    x = 0;

    logger.info("entering answer validation mode...");

    for a in anyhead_gen(f_type[F_PSEUDO_ANS], qst1 [nav.webmap["qmap"]["ans"]]):

        qst1 [nav.webmap["qmap"]["ans"]] = a;
        preq[F_QKEY] = qst1;

        x = submit(nav, preq, **kwargs);
        if x == SUBMIT_RETRY_FETCH:
            return x;

        elif x == 1:
            qst [nav.webmap["qmap"]["ans"]] = a;
            preq[F_QKEY] = qst;
            x = submit(nav, preq, **kwargs);

            if x == 0:
                if amgr:
                    amgr.check(qst, x);
                return status.Status(status.S_FATAL, "detected answer is problematic", (preq, qst));

            elif x == 1:
                if fp and fp.writable():
                    fp.reconfigure(encoding = f_type[F_ENCODING]);
                    fp.write("%s. %s\n\n" % (qst[nav.webmap["qmap"]["qn"]],
                            qst[nav.webmap["qmap"]["qdescr"]]));
                    
                    for i1, a1 in enumerate(f_type[F_PSEUDO_ANS]):
                        opt = b'opt';
                        opt += bytes([65 + i1]);
                        fp.write("\t");

                        if a == a1:
                            fp.write("--->> %s\n\n" %
                                    (qst[nav.webmap["qmap"][opt.decode().lower()]],));
                        else:
                            fp.write("      %s\n\n" % (qst[nav.webmap["qmap"][opt.decode().lower()]],));

                if amgr:
                    amgr.check(qst, x);

                return status.Status(status.S_OK, "success", qst);
            else:
                return x;

        elif not brute_safe(nav, usr, qst, **kwargs):
            return status.Status(status.S_FATAL, "unable to brute for the answers from the server", qst);



def answer_strict(qst, amgr):
    try:
        x = copy (qst);

        x = amgr.answer (x);

        if x and x != ansm.ANS_NOANSWER and qst [qmgr.qmap ["qid"]] == x [qmgr.qmap ["qid"]]:
            return x;

        return status.Status(status.S_NULL, "can't answer", (qst, amgr));

    except BaseException as err:
        return status.Status(status.S_NULL, "can't answer", (qst, amgr));


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

def cache_put(data, page, sl = None):
    if not CACHE_PAGE_CACHE or not isinstance(CACHE_PAGE_CACHE, (str,
        pathlib.Path)) or not isinstance(data[1], requests.Response):
        return None;

    cdir = pathlib.Path(CACHE_PAGE_CACHE);
    cdir.mkdir(parents = True, exist_ok = True);
    target = cdir.joinpath(page + (".html" if sl == None else "%s.json" % (sl,)));

    if sl == None:
        if not target.exists() or CACHE_OVERWRITE:
            target.write_bytes(data.content);

    else:
        fro_page = cdir.joinpath(page + "%s.html" % (sl,));

        if not target.exists() or not fro_page.exists() or CACHE_OVERWRITE:
            cont = requests.structures.OrderedDict(
                    ("to", data[0]),
                    );

            fro = requests.structures.OrderedDict();
            fro["url"] = data[1].url;
            fro["content"] = str(data[1].text);
            cont["fro"] = fro;

            target.write_text(json.dumps(cont, default = dict, indent = 4));
            fro_page.write_text(data[1].text);

    return True;

def cache_get(page, sl = None):
    if not CACHE_PAGE_CACHE or not isinstance(CACHE_PAGE_CACHE, (str,
        pathlib.Path)):
        return None;

    cdir = pathlib.Path(CACHE_PAGE_CACHE);
    cdir.mkdir(parents = True, exist_ok = True);
    target = cdir.joinpath(page + (".html" if sl == None else "%s.json" % (sl,)));

    if not target.exists():
        return None;
    
    # res is initialized based on its implementation on the 'requests' library,
    # this ain't sustainable

    res = requests.Response();
    res.status_code = 200;
    res.reason = "OK";

    if sl == None:
        res._content = target.read_bytes();
        res.request = requests.Request();
        return res;

    else:
        data = json.loads(read_file_text(target));
        if "to" not in data or ("fro" not in data or "url" not in data["fro"]):
            return None;

        res.url = data["fro"]["url"];

        if "content" in data["fro"]:
            # too general encoding
            res._content = bytes(data["fro"]["content"], encoding = "utf-8");

        return [data["to"], res];



def goto_page3(*pargs, **kwargs):
    
    lres = None;

    retry = MAX_RETRIES;
    while True:
        try:
            lres = requests.request(*pargs, **kwargs);
            #lres.raise_for_status();

            return lres;

        except Exception as err:

            if isinstance(err, (
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout
                )) and not isinstance(err.args[0], urllib3.exceptions.MaxRetryError):
                retry -= 1;

            elif isinstance(err, requests.exceptions.RequestException):
                if not unknown_err_handler_hook(err, lres):
                    return status.Status(status.S_ERROR, "unknown err while sending to server", (lres, err));


                retry -= 1;

            else:
                raise err;


    return status.Status(status.S_ERROR, "maximum retries exceeded for sending to server", lres);


def just_goto_page(session = requests, *req, **kwargs):

    logger.debug(
            "just_goto_page: preparing for a pure request, only network issues will be handled"
            );

    lres = None;

    while True:
        try:
            lres = session.request(*req, **kwargs);

            return lres;

        except Exception as err:

            if isinstance(err, (
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout
                )) and not isinstance(err.args[0], urllib3.exceptions.MaxRetryError):
                pass;

            elif isinstance(err, requests.exceptions.RequestException):
                if not unknown_err_handler_hook(err, lres):
                    logger.debug("halting...");
                    return status.Status(status.S_ERROR, "unknown err while sending to server", (lres, err));


            else:
                raise err;


    return status.Status(status.S_ERROR, "maximum retries exceeded for sending to server", lres);



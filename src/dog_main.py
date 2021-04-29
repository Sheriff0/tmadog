import time
import math
import unittest
import argparse
import sys
import urllib.parse
import re
import requests
import navigation
import configparser
import ansm
import dbm
import lxml
import scrm
import copy
import json
import cloudscraper
import cookie_parse
import qstwriter
import pathlib
import os

import logging
import libdogs
import simple_dog
import status

import nourc


import uuid
import dropbox
import threading

import dog_idl

VERSION = 1.00;
GEOMETRY = '400x400+100+100';

CANONICAL_URL = "https://www.nouonline.net";

CHK_QUIT = False;
CHK_FAIL = None;
CHK_SUCCESS = dropbox.KeyInfo;

class DummyQueue:
    def __init__(self, *tasks):
        self._queue = [];
        self._queue.extend(tasks);

    def pop(self, tcount = 1):
        lres = None;

        while tcount > 0:
            # Perharps, to make atomic the checking of the queue and popping of a task.
            try:
                tcall = self._queue.pop();
                lres = tcall();
            except IndexError:
                pass;

            tcount -= 1;
        
        return lres;

    def put(self, task, *pargs, **kwargs):
        return task();


def getkey(retry = False):

    user_key = None;
    ts = None;
    win = None;
    ret = CHK_FAIL;
    msg = "Please input your key" if not retry else "Invalid or expired key. Please input a key.";

    def _quit():
        nonlocal ret, win;
        ret = CHK_QUIT;
        win.destroy();

    def vfunc(val):
        nonlocal btn, ukey;
        if val:
            btn["state"] = "normal";
        else:
            btn["state"] = "disabled";

        return 1;

    try:
        import tkinter, tkinter.messagebox, tkinter.filedialog, tkinter.font

        win = tkinter.Tk();
        win.geometry(GEOMETRY);
        win.title("TMADOG %d" % (VERSION,));
        win.protocol("WM_DELETE_WINDOW", _quit);
        ukey = tkinter.StringVar();

        kentry = tkinter.Entry(win, width = 16, textvariable = ukey, validate = "key", validatecommand = (win.register(vfunc), '%P'));

        btn = tkinter.Button(text = "Enter", command = lambda : win.destroy(), font = tkinter.font.Font(family="Arial", size = 40, weight =
                    "bold"), background = "green", state = "disabled");

        kentry.place(x = 0, y = 0, relwidth = 1, relheight = 1/10);

        tkinter.Label(win, text = msg, font = "courier").place(rely = 1/10, x = 0, relwidth = 1);

        btn.place(rely = 1/2, x = 0, relwidth = 1, relheight = 1/2);

        win.bind("<Return>", lambda e: win.destroy() if ukey.get() else None);

        kentry.focus();
        win.mainloop();
        user_key = ukey.get();

        dropbox.libdogs.init_hooks(err_hook = unknown_err_handler());

        win = tkinter.Tk();
        win.withdraw();

    except ModuleNotFoundError:
        try:
            user_key = input("\n%s->> " % (msg,));
        except KeyboardInterrupt:
            ret = CHK_QUIT;

    if not user_key or ret == CHK_QUIT:
        if win:
            win.destroy();

        return ret;

    print("checking key %s" % (user_key,));

    try:
        ts = dropbox.alloc_key(user_key);
    except KeyboardInterrupt:
        ts = None;
        ret = CHK_QUIT;

    if win:
        win.destroy();

    if not ts:
        return ret;

    return ts;


def write_keyfile(fp, st, base = 8):

    fp = open(fp, "w");
    byt_str = "";
    for c in st:
        if base == 2:
            b = str(bin(ord(c)))[2:];
            byt_str += "%s%s" % ("0" * (8 - len(b)), b);
        elif base == 8:
            byt_str += "%03o" % (ord(c),);
        elif base == 16:
            byt_str += "%02x" % (ord(c),);
        else:
            fp.close();
            return False;

    fp.write(byt_str);
    fp.close();
    return True

def read_keyfile(fi, base = 8):
    base_to_maxbyte_widthtable3 = {
            2:  [8, "0b"],
            8:  [3, "0o"],
            16: [2, "0x"],
            };

    if not base in base_to_maxbyte_widthtable3:
        return False;

    bytes_st = libdogs.read_file_text(fi);
    st = "";
    ln = len(bytes_st);
    idx = 0;
    g = base_to_maxbyte_widthtable3[base][0];

    while idx < ln:
        st += chr(
                int(
                    base_to_maxbyte_widthtable3[base][1] + bytes_st[idx:idx+g],
                    base
                    )
                );
        idx += g;

    return st;

def key_init(pkg_name, retry = False):

    pkg_dir = pathlib.Path(pkg_name).parent;
    keyf = pkg_dir.joinpath(".dogger");
    kt = getkey(retry);

    if not kt:
        return kt;

    kfile = pkg_dir.joinpath("." + str(kt));
    write_keyfile(str(kfile), json.dumps(kt));
    write_keyfile(str(keyf), "%s" % (str(kfile.resolve()),));
    return kt;

def checks(pkg_name, retry = False):
    pkg_dir = pathlib.Path(pkg_name).parent;
    keyf = pkg_dir.joinpath(".dogger");

    if not keyf.exists():
        return key_init(pkg_name, retry);

    else:
        kfile = read_keyfile(str(keyf));
        
        kres = CHK_FAIL;

        try:
            lparam = json.loads(read_keyfile(kfile));
            key = pathlib.Path(kfile).stem[1:];
            return dropbox.KeyInfo(key, lparam);
        except BaseException:
            print("invalid key file");

            return key_init(pkg_name, retry = True) if kres != CHK_SUCCESS else kres;



def mkstat_tab(dog):
    stat_tab = {};
    for st in simple_dog.dog_submit_stat(dog):
        arg = st[simple_dog.STAT_ARG];
        u, c, t = arg[libdogs.P_USR], arg.get(libdogs.P_CRSCODE, "nil"), arg[libdogs.P_TMA];

        hsh = "%s%s%s" % (u, c, t);
        stat_tab[hsh.lower()] = st;

    return stat_tab;



def write_stat_raw(itr, fi):
    col_max = 4;
    ok = 0;
    sta = "";
    not_ok = 0;
    ok_str = "# Submitted quizes:";
    not_ok_str = "# Quizes not submitted:";
    with open(fi, "w") as fp:
        for st in itr.values():
            arg = st[simple_dog.STAT_ARG];
            line = "" if st[simple_dog.STAT_ST].code >= status.S_INT else "# ";
            if not arg.get(libdogs.P_CRSCODE, None):
                arg[libdogs.P_CRSCODE] = "nil";
            line += "--matno %s --pwd %s --crscode %s --tma %s --url %s\n" % (arg[libdogs.P_USR], arg[libdogs.P_PWD], arg[libdogs.P_CRSCODE], arg[libdogs.P_TMA], arg[libdogs.P_URL]);

            line += "# %s\n\n" % (st[simple_dog.STAT_ST].msg,);
            sta += line;

            if st[simple_dog.STAT_ST].code >= status.S_INT:
                not_ok_str += "\n#\t%s" % (arg[libdogs.P_CRSCODE],) if (not_ok % col_max) == 0 else "  %s" % (arg[libdogs.P_CRSCODE],);
                not_ok_str += "(%s,%s)" % (arg[libdogs.P_USR], arg[libdogs.P_TMA]) ;
                not_ok += 1;

            else:
                ok_str += "\n#\t%s" % (arg[libdogs.P_CRSCODE],) if (ok % col_max) == 0 else "  %s" % (arg[libdogs.P_CRSCODE],);
                ok_str += "(%s,%s)" % (arg[libdogs.P_USR], arg[libdogs.P_TMA]) ;
                ok += 1;

        ok_str += "\n\n#total submitted: %s\n\n" % (ok,);
        not_ok_str += "\n\n#total not submitted: %s\n\n" % (not_ok,);
        tfp = open(
                str(pathlib.Path(fi).parent.joinpath("stat-%s.txt" %
                    (math.trunc(time.time()),)).resolve()),
                "w"
                );
        tfp.write(ok_str);
        tfp.write(not_ok_str);
        tfp.write(sta);
        tfp.close();
        fp.write(ok_str);
        fp.write(not_ok_str);
        fp.write(sta);


def mkstat(dog, fi):
    crsreg = {};
    col_max = 4;
    ok = 0;
    sta = "";
    not_ok = 0;
    ok_str = "# Submitted quizes:";
    not_ok_str = "# Quizes not submitted:";
    with open(fi, "w") as fp:
        for st in simple_dog.dog_submit_stat(dog):
            arg = st[simple_dog.STAT_ARG];
            if not arg.get(libdogs.P_CRSCODE, None):
                arg[libdogs.P_CRSCODE] = "nil";

            crsreg.setdefault(arg[libdogs.P_CRSCODE].lower(), set());
            crsreg[arg[libdogs.P_CRSCODE].lower()].add(arg[libdogs.P_USR].upper());

            line = "" if st[simple_dog.STAT_ST].code >= status.S_INT else "# ";
            line += "--matno %s --pwd %s --crscode %s --tma %s --url %s\n" % (arg[libdogs.P_USR], arg[libdogs.P_PWD], arg[libdogs.P_CRSCODE], arg[libdogs.P_TMA], arg[libdogs.P_URL]);

            line += "# %s\n\n" % (st[simple_dog.STAT_ST].msg,);
            sta += line;

            if st[simple_dog.STAT_ST].code >= status.S_INT:
                not_ok_str += "\n#\t%s" % (arg[libdogs.P_CRSCODE],) if (not_ok % col_max) == 0 else "  %s" % (arg[libdogs.P_CRSCODE],);
                not_ok_str += "(%s,%s)" % (arg[libdogs.P_USR], arg[libdogs.P_TMA]) ;
                not_ok += 1;

            else:
                ok_str += "\n#\t%s" % (arg[libdogs.P_CRSCODE],) if (ok % col_max) == 0 else "  %s" % (arg[libdogs.P_CRSCODE],);
                ok_str += "(%s,%s)" % (arg[libdogs.P_USR], arg[libdogs.P_TMA]) ;
                ok += 1;

        ok_str += "\n\n#total submitted: %s\n\n" % (ok,);
        not_ok_str += "\n\n#total not submitted: %s\n\n" % (not_ok,);
        tfp = open(
                str(pathlib.Path(fi).parent.joinpath("stat-%s.txt" %
                    (math.trunc(time.time()),)).resolve()),
                "w"
                );
        tfp.write(ok_str);
        tfp.write(not_ok_str);
        tfp.write(sta);
        tfp.close();

        fp.write(ok_str);
        fp.write(not_ok_str);
        fp.write(sta);

    return crsreg;


class Wlist_Handler(dropbox.KeyInfo):
    def __init__(self, key, *pargs, **kwargs):
        if isinstance(key, dropbox.KeyInfo):
            pargs = list(pargs);
            pargs.insert(0, key);
            key = str(key);

        self.path = kwargs.pop("lpath", ".");
        super().__init__(key, *pargs, **kwargs);
        rkinfo = dropbox.fetch_keyinfo(str(self.key));


        if rkinfo and rkinfo.get("mtime", 0) > self.get("mtime", 0):
            self.update(rkinfo);
        
            if "whitelist" in self:
                self["whitelist"] = dropbox.Whitelist(self["whitelist"]);
    
    def __call__(self, wlist):
        self["whitelist"] = wlist;
        try:
            write_keyfile(
                    str(
                        pathlib.Path(
                            self.path
                            ).joinpath(
                                ".%s" % (self.key,)
                                ).resolve()
                            ),
                    json.dumps(self)
                    );

            return dropbox.update_key(self);
        except BaseException:
            return False;


def main (parser, pkg_name, argv, kinfo = None):

    if kinfo and not dropbox.fetch_keyinfo(str(kinfo)):
        print("Please renew your package as the current package has expired");
        return False;

    pkg_name = pathlib.Path(pkg_name);

    pkg_dir = pkg_name if pkg_name.is_dir() else pkg_name.parent;

    wlist_h = Wlist_Handler(kinfo, lpath = str(pkg_dir.resolve()));

    logger = logging.getLogger('tmadog');

    logger.setLevel(logging.DEBUG);
    # create file handler which logs even debug messages
    dfh = logging.FileHandler(str(pkg_dir.joinpath('debug.log')), mode = "w");
    dfh.setLevel(logging.DEBUG);

    fatal = logging.FileHandler(str(pkg_dir.joinpath('fatal.log')), mode = "w");
    fatal.setLevel(logging.CRITICAL);

    stdout = logging.StreamHandler();
    stdout.setLevel(logging.INFO);

    dfh.setFormatter(logging.Formatter('%(asctime)s: %(name)s: %(levelname)s: %(message)s'));

    stdout.setFormatter(logging.Formatter('%(name)s: %(levelname)s: %(message)s'));

    # add the handlers to the logger
    logger.addHandler(dfh);
    logger.addHandler(fatal);
    logger.addHandler(stdout);

    argv, rest = collapse_file_argv(parser, argv, prep_hypen);
    argv.extend(rest);

    args = parser.parse_args(argv);

    lastcookie = args.cookies;

    def getcookie(nav):

        if not args.cookies:
            fi = pathlib.Path(input("""

Please input a cookie file (e.g from the browser)--> """));

            if not isinstance(fi, str) or re.match(r'\s*', fi):
                if not lastcookie:
                    return nav;

                fi = lastcookie;


        else:
            fi = pathlib.Path(args.cookies);
            args.cookies = None;

        session = libdogs.session_from_cookies(nav.keys[libdogs.P_URL], str(fi));
        if session:
            nav.session = session;
        return nav;


    def get_nav(cli):
        nonlocal dog;
        if dog.nav:
            if not re.match(dog.nav.keys[libdogs.P_USR], cli[libdogs.P_USR], re.I):
                nav = dog.nav;
                dog.nav = libdogs.lazy_nav_reconf(nav, cli);
        else:
            nav = navigation.Navigator(cli[libdogs.P_URL], cli[libdogs.P_WMAP], cli);
            nav = getcookie(nav);
            dog.nav = nav;

        return dog.nav;

    def cleanup():
        nonlocal stime;

        f = open (args.qstdump, 'w') if args.debug else None

        crsreg = mkstat(dog, args.stats);

        if args.updatedb:
            dbm.update_hacktab (args.database, ansmgr.iter_cache (),
                    ansmgr.qmap, fp = f);
        #if args.debug or args.output:
        #    arr = []
        #    for qst in ansmgr.iter_cache ():
        #       arr.append (qst)

        #    if args.debug:
        #        json.dump (arr, f)

            #if args.output:
            #    qstwriter.fromlist(arr, ansmgr.qmap, qstwriter.writeqst(args.output, crsreg));

        if f:
            f.close ()

        if ansmgr._cur:
            ansmgr.close ()


        etime = time.time();
        diff = etime - stime;
        hr,diff = divmod(diff, 60*60);
        mn,diff = divmod(diff, 60);


        print("\n\nfinished job in %s hour(s), %s min(s) and %s sec(s)" %
                (
                   math.trunc(hr),
                   math.trunc(mn),
                   math.trunc(diff),
                    )
                );

    logger.info("Welcome to tmadog version %s\n" % (VERSION,));

    if not getattr(args, "stats"):
        logger.info("no stat file given, setting default stat file");
        setattr(args, "stats", str(pkg_dir.joinpath("dog.stat.txt")));


    if not getattr(args, libdogs.P_WMAP):
        logger.info("no config file given, setting default config file for webmap");
        setattr(args, libdogs.P_WMAP, str(pkg_dir.joinpath("nourc")));

    mp = configparser.ConfigParser (interpolation =
        configparser.ExtendedInterpolation ())

    logger.info("reading config file and initializing a webmap");
    #mstr = libdogs.read_file_text(getattr(args, libdogs.P_WMAP));
    mp.read_string (nourc.rc);

    setattr(args, libdogs.P_WMAP, mp);

    if not args.database:
        logger.info("no database file given, setting default database file for webmap");
        args.database = str(pkg_dir.joinpath("noudb"));

    if not args.cache:
        logger.info("no cache dir given, setting default cache directory for quiz");
        args.cache = str(pkg_dir.joinpath("dog_cache"));

    if not args.output:
        logger.info("no output file given, setting default output file for quiz");

        #NOTE the unix-style though.
        args.output = str(pkg_dir.joinpath("output/{matno}_{crscode}_TMA{tmano}.txt"));

    pathlib.Path(args.output).parent.resolve().mkdir(parents = True, exist_ok = True);

    logger.debug("initializing answer manager");
    ansmgr = ansm.AnsMgr (
            qmap = mp['qmap'],
            database = args.database,
            mode = ansm.ANS_MODE_NORM,
            pseudo_ans = mp['qmap']['pseudo_ans'].split (','),
            )

    logger.debug("initializing a dog to run task");
    libdogs.init_hooks(cookie_hook = getcookie, nav_hook = get_nav);

    libdogs.CACHE_PAGE_CACHE = args.cache;
    libdogs.CACHE_CACHE_FIRST = args.cache_first;
    libdogs.CACHE_OVERWRITE = args.overwrite;
    dog = simple_dog.SimpleDog(
            libdogs.preprocess(
                args,
                args.exclude if args.exclude else [], # NOTE defaults like
                # this should be in config
                **wlist_h,
                wlist_cb = wlist_h,
                ),
            ansmgr,
            get_nav,
            outfile = args.output
            );

    try:
        task = dog._InternalTask(cmd = None, args = args);
        stime = time.time();

        dog.submit(task);
        cleanup();

    except KeyboardInterrupt:
        cleanup();

    except BaseException as err:
        cleanup();
        raise err;



class ScrCtrl:
    def disable(self):
        pass;

    def enable(self):
        pass;


ARG_QUIT = None;
ARG_COMPLETE = True;
ARG_INCOMPLETE = False;


def validate_entry(eprof, cb = None):
    def _val(val):
        if cb and callable(cb):
            cb(eprof, val);

        return 1;

    return _val;

def hinter(eprof, cb = None):
    def _h(e):
        if eprof["ign_hint"]:
            return;
        eprof["val"].set(eprof["hint"]);

        if cb and callable(cb):
            return cb(eprof);

    return _h;

def unhint(eprof, cb = None):
    def _uh(e):
        if eprof["ign_hint"]:
            return;
        eprof["val"].set("");

        if cb and callable(cb):
            return cb(eprof);

    return _uh;


def gf(eprof, win, cb = None):
    import tkinter.filedialog

    def _gf(e):
        win.focus();
        v = tkinter.filedialog.askopenfilename(master = win, title = eprof["name"]);
        #Remove focus from the invoking widget
        if v:
            eprof["val"].set(v);

        if cb and callable(cb):
            return cb(eprof);

    return _gf;


def mkmenu(pscr):
    pscr.option_add('*tearOff', tkinter.FALSE);
    menu = tkinter.Menu(pscr);
    elp = tkinter.Menu(menu);
    elp.add_command(label = 'Cookie file', command = lambda: tkinter.messagebox.showinfo(title = "World", message = "Hello, World!", detail = "xxx"));
    elp.add_command(label = 'TMA file', command = lambda: tkinter.messagebox.showinfo(title = "World", message = "Hello, World!"));
    elp.add_command(label = 'WEBSITE', command = lambda: tkinter.messagebox.showinfo(title = "World", message = "Hello, World!", detail = "xxx"));
    elp.add_command(label = 'TMA NO', command = lambda: tkinter.messagebox.showinfo(title = "World", message = "Hello, World!", detail = "xxx"));
    elp.add_command(label = 'COURSE CODE', command = lambda: tkinter.messagebox.showinfo(title = "World", message = "Hello, World!", detail = "xxx"));
    
    menu.add_cascade(menu = elp, label = "Help");

    pscr["menu"] = menu;


def factory_gui2argv(pscr, parser, *pargs):
    import dog_idl
   
    FROM_TMAFILE = "From TMA file";
    FROM_CMDLINE = "From Command line";

    pseudo_values = {
            FROM_CMDLINE: None,
            FROM_TMAFILE: None,
            };

    psr = libdogs.DogCmdParser ();

    psr.add_argument ('--tma', action = libdogs.AppendList);

    psr.add_argument ('--url', action = libdogs.AppendList);

    psr.add_argument ('--cookies');

    psr.add_argument ('--crscode', action = libdogs.AppendList);

    arg0, rest0 = psr.parse_known_args(pargs);

    if not arg0.url:
        arg0.url = "https://www.nouonline.net";

    if not arg0.tma:
        arg0.tma = "1";

    ## to grab '@ '-prefixed tma files
    # NOTE: this is an argparse hack, things could break in future versions of
    # the library.

    psr = libdogs.DogCmdParser(prefix_chars = parser.fromfile_prefix_chars);
    
    psr.add_argument (parser.fromfile_prefix_chars, action = libdogs.AppendList, dest = "tmafile");
    argf, rest1 = psr.parse_known_args(rest0);

    if not argf.tmafile:
        argf.tmafile = [];

    ## to grab '@'-prefixed tma files
    
    rest2 = [];
    for af in rest1:
        if not af.startswith(parser.fromfile_prefix_chars):
            rest2.append(af);
            continue;

        argf.tmafile.append(af[1:]);

    # IF_OPTIONS-typed inputs are positioned at an odd index(i.e (index%2) ==1).
    # this is to ease some sort of future processing.

    ifds = [
            {
                dog_idl.IFD_DEFAULT: arg0.url,
                dog_idl.IFD_NAME: "WEBSITE",
                dog_idl.IFD_REQUIRED: True,
                dog_idl.IFD_PREFIX: "--url ",
                },

            {
                dog_idl.IFD_DEFAULT: arg0.crscode,
                dog_idl.IFD_NAME: "COURSE-CODE",
                dog_idl.IFD_CHOICES: ("All", FROM_TMAFILE, FROM_CMDLINE),
                dog_idl.IFD_REQUIRED: True,
                dog_idl.IFD_PREFIX: "--crscode ",
                dog_idl.IFD_TYPE: dog_idl.IF_OPTIONS,
                dog_idl.IFD_PSEUDOS: pseudo_values,
                },

            ## tmafile
            {
                dog_idl.IFD_DEFAULT: argf.tmafile,
                dog_idl.IFD_NAME: "TMA File",
                dog_idl.IFD_HINT: "File containing matric numbers and passwords",
                dog_idl.IFD_REQUIRED: True,
                dog_idl.IFD_PREFIX: parser.fromfile_prefix_chars,
                dog_idl.IFD_TYPE: dog_idl.IF_FILE,
                },

            {
                dog_idl.IFD_DEFAULT: arg0.tma,
                dog_idl.IFD_CHOICES: ("1", "2", "3", FROM_TMAFILE, FROM_CMDLINE),
                dog_idl.IFD_NAME: "TMA NO.",
                dog_idl.IFD_REQUIRED: True,
                dog_idl.IFD_PREFIX: "--tma ",
                dog_idl.IFD_TYPE: dog_idl.IF_OPTIONS,
                dog_idl.IFD_PSEUDOS: pseudo_values,
                },

            {
                dog_idl.IFD_DEFAULT: arg0.cookies,
                dog_idl.IFD_HINT: "file downloaded from a browser",
                dog_idl.IFD_NAME: "COOKIE-FILE",
                dog_idl.IFD_PREFIX: "--cookies ",
                dog_idl.IFD_TYPE: dog_idl.IF_FILE,
                },

            ];


    ifdlen = len(ifds); 
    gui2argv = dog_idl.Gui2Argv(pscr, *ifds);
    
    cmdline_used = False;

    class _GuiProxy:
        def __getattribute__(self, name):
            nonlocal cmdline_used;
            if name == "get_argv":
                if not cmdline_used:
                    cmdline_used = True;
                    return gui2argv.get_argv_with_all_defaults;

                else:
                    return gui2argv.get_argv;

            elif name == "get_cmdline":
                if not cmdline_used:
                    cmdline_used = True;
                    return gui2argv.get_cmdline_with_all_defaults;

                else:
                    return gui2argv.get_cmdline;

            else:
                return getattr(gui2argv, name);

    return _GuiProxy();


def gui_getfile(cb, title = None):
    import tkinter, tkinter.ttk, tkinter.filedialog

    def _get():
        fp = tkinter.filedialog.askopenfilename(title = title);

        if cb and callable(cb):
            return cb(fp);

    return _get;


def GuiLogger(scr, logger, cb = None, height = 30, width = 100):

    import tkinter, tkinter.ttk, tkinter.scrolledtext

    log = None;
    win = None;
    ltext = [];
    initiator = None;

    def info(msg, *pargs, **kwargs):
        nonlocal log, ltext;

        msg1 =  msg % pargs;

        if len(ltext) == 50:
            ltext.pop(0);

        ltext.append(msg1);

        if log:
            numlines = log.index('end - 1 line').split('.')[0];
            log['state'] = 'normal';
            if numlines == height:
                log.delete(1.0, 2.0);

            if log.index('end-1c') != '1.0':
                log.insert('end', '\n');

            log.insert('end', "info: %s" % msg1);
            log['state'] = 'disabled';
            log.see("end-1c linestart");


        return logger.info(msg, *pargs, **kwargs);

    def flush():
        nonlocal ltext, log;
        log['state'] = 'normal';

        for msg in ltext:

            if log.index('end-1c') != '1.0':
                log.insert('end', '\n');

            log.insert('end', "info: %s" % msg);

        log['state'] = 'disabled';

        log.see("end-1c linestart");


    def destroy():
        nonlocal win, log, ltext;
        win.destroy();
        win = None;
        log = None;
        ltext = [];
        if initiator and isinstance(initiator, ScrCtrl):
            initiator.enable();

    class _Logger:
        def __call__(self, *pargs, **kwargs):
            nonlocal log, win, initiator, cb;
            if win == None:
                win = tkinter.Toplevel(scr);
                win.protocol("WM_DELETE_WINDOW", destroy);
                log = tkinter.scrolledtext.ScrolledText(win, background = "black", foreground = "white", state='normal', height=height);
                log.rowconfigure(0, weight = 1);
                log.columnconfigure(0, weight = 1);

                flush();

                log.grid(column = 0, row = 0, sticky = (tkinter.N, tkinter.S, tkinter.W, tkinter.E));

                initiator = kwargs.pop("initiator", None);

                if initiator and isinstance(initiator, ScrCtrl):
                    initiator.disable();

                if cb and callable(cb):
                    cb(*pargs, logger = self, window = win, destroy = destroy, **kwargs);



            elif win.state() == "iconic":
                win.deiconify();


        def __getattribute__(self, name):
            nonlocal info;
            if name == "info":
                return info;

            else:
                return getattr(logger, name);

    return _Logger();


def gui_getcookie(default = None, attr = None, queue = DummyQueue(), cb = None):

    import tkinter.messagebox, tkinter.filedialog

    def _getcookie(nav):
        print("\n\nCookies have expired. Check the main screen to resolve this.\n\n");

        task = dog_idl.Task(tkinter.messagebox.askyesnocancel, title = "Cookie File",
                icon = "question", message = "Cookies needed. Do you want to continue with your previous cookie file", detail = "click no to choose a file, click yes to use previous file. click cancel to exit the program");

        queue.put(task);
        res = task.wait();

        if res == None:
            raise KeyboardInterrupt();

        if not res:
            task = dog_idl.Task(tkinter.filedialog.askopenfilename, title = "Cookie File");
            res = task.wait();

        if not res or res == True:
            if default and not isinstance(default, str) and attr:
                res = getattr(default, attr);

            elif default and isinstance(default, str):
                res = default;


        if not res or (not isinstance(res, str) or re.match(r'\s+', res)):
            return nav;


        fi = pathlib.Path(res);

        session = libdogs.session_from_cookies(nav.keys[libdogs.P_URL], str(fi));

        if session:
            nav.session = session;

        if cb and callable(cb):
            cb(res);

        return nav;

    return _getcookie


def unknown_err_handler(queue = DummyQueue()):
    def _unknown_err_handler(err, *pargs):
        import tkinter.messagebox, tkinter.filedialog

        print("\n\nAn unknown, possibly network, error occured. Check the main screen to resolve this.\n\n");
        
        task = dog_idl.Task(tkinter.messagebox.askretrycancel, title = "Error",
                icon = "error", message = "An error occured", detail = "%s" % (err,));

        queue.put(task);
        res = task.wait();


        if res:
            return status.Status(status.S_OK, "continue action", err);
        else:
            raise KeyboardInterrupt();
    
    return _unknown_err_handler;


def iter_file_argv(*argfl):
    
    for argf in argfl:
        args = libdogs.read_file_text(argf);
        for arg_line in args.split("\n"):
            if not re.match(r'^\s*#.*', arg_line):
                ar = arg_line.split();
                for a1 in ar:
                    yield a1;



def collapse_file_argv(parser, argv, preproc = lambda a,b: a):
    aid = parser.fromfile_prefix_chars;
    if not aid:
        return [];

    arg_res = [];
    rest = [];

    for arg in argv:
        if not isinstance(arg, str) or not arg.startswith(aid):
            rest.append(arg);
            continue;

        ar = iter_file_argv(arg[1:]);
        arg_res.extend(preproc(ar, 0));

    return (arg_res, rest);


def prep_hypen(args, idx):
    argr = [];
    el = 0;
    args = iter(args);
    for a in args:

        if a.startswith("-"):
            argr.extend([a, next(args)]);
            if not a.startswith(("--matno", "--pwd")):
                continue;

        elif el == 0 or not el % 4:
            argr.extend(["--matno", a]);
        else:
            argr.extend(["--pwd", a]);

        el += 2;

    return argr;

def gui_start(parser, pkg_name, logger, *argv, **kwargs):
    wlist_h = kwargs.pop("wlist_h", None);
    queue = kwargs.pop("queue", None);

    #if wlist_h and not dropbox.fetch_keyinfo(str(wlist_h)):
    #    print("Please renew your package as the current package has expired");
    #    return False;

    pkg_name = pathlib.Path(pkg_name);

    pkg_dir = pkg_name if pkg_name.is_dir() else pkg_name.parent;

    args = kwargs.pop("args", None);
    dog = kwargs.pop("dog", None);

    if not args:
        logger.info("Welcome to TMADOG version %s\n" % (VERSION,));

        aid = parser.fromfile_prefix_chars if parser.fromfile_prefix_chars else "";

        argr, rest = collapse_file_argv(parser, argv, prep_hypen);
        argr.extend(rest);

        args,ex = parser.parse_known_args(argr);


    def get_nav(cli):
        nonlocal dog, getcookie;
        if dog.nav:
            if not re.match(dog.nav.keys[libdogs.P_USR], cli[libdogs.P_USR], re.I):
                nav = dog.nav;
                dog.nav = libdogs.lazy_nav_reconf(nav, cli);
        else:
            nav = navigation.Navigator(cli[libdogs.P_URL], cli[libdogs.P_WMAP], cli);
            session = libdogs.session_from_cookies(nav.keys[libdogs.P_URL], args.cookies);
            if session:
                nav.session = session;

            dog.nav = nav;

        return dog.nav;


    def cleanup():
        nonlocal stime;

        f = open (args.qstdump, 'w') if args.debug else None

        if args.updatedb:
            dbm.update_hacktab (args.database, ansmgr.iter_cache (),
                    ansmgr.qmap, fp = f);
        #if args.debug or args.output:
        #    arr = []
        #    for qst in ansmgr.iter_cache ():
        #       arr.append (qst)

        #    if args.debug:
        #        json.dump (arr, f)

            #if args.output:
            #    qstwriter.fromlist(arr, ansmgr.qmap, qstwriter.writeqst(args.output, crsreg));

        if f:
            f.close ()

        if ansmgr._cur:
            ansmgr.close ()


        etime = time.time();
        diff = etime - stime;
        hr,diff = divmod(diff, 60*60);
        mn,diff = divmod(diff, 60);

        logger.info("\n\nfinished job in %s hour(s), %s min(s) and %s sec(s)" %
                (
                   math.trunc(hr),
                   math.trunc(mn),
                   math.trunc(diff),
                    )
                );


    if not getattr(args, "stats"):
        logger.info("no stat file given, setting default stat file");
        setattr(args, "stats", str(pkg_dir.joinpath("dog.stat.txt")));


    if not getattr(args, libdogs.P_WMAP):
       #logger.info("no config file given, setting default config file for webmap");
        setattr(args, libdogs.P_WMAP, str(pkg_dir.joinpath("nourc")));

        mp = configparser.ConfigParser (interpolation =
            configparser.ExtendedInterpolation ())

        logger.info("reading config file and initializing a webmap");
        #mstr = libdogs.read_file_text(getattr(args, libdogs.P_WMAP));
        mp.read_string (nourc.rc);

        setattr(args, libdogs.P_WMAP, mp);

    mp = getattr(args, libdogs.P_WMAP);

    if not args.database:
        logger.info("no database file given, setting default database file for webmap");
        args.database = str(pkg_dir.joinpath("noudb"));

    if not args.cache:
        logger.info("no cache dir given, setting default cache directory for quiz");
        args.cache = str(pkg_dir.joinpath("dog_cache"));

    if not args.output:
        logger.info("no output file given, setting default output file for quiz");

        #NOTE the unix-style though.
        args.output = str(pkg_dir.joinpath("output/{matno}_{crscode}_TMA{tmano}.txt"));

    pathlib.Path(args.output).parent.resolve().mkdir(parents = True, exist_ok = True);


    def update_cookie(f):
        nonlocal args;
        args.cookies = f;


    logger.debug("initializing answer manager");
    ansmgr = ansm.AnsMgr (
            qmap = mp['qmap'],
            database = args.database,
            mode = ansm.ANS_MODE_NORM,
            pseudo_ans = mp['qmap']['pseudo_ans'].split (','),
            )


    logger.debug("initializing a dog to run task");

    libdogs.CACHE_PAGE_CACHE = args.cache;
    libdogs.CACHE_CACHE_FIRST = args.cache_first;
    libdogs.CACHE_OVERWRITE = args.overwrite;

    ndog = simple_dog.SimpleDog(
            libdogs.preprocess(
                args,
                args.exclude if args.exclude else [], # NOTE defaults like
                # this should be in config
                **wlist_h,
                wlist_cb = wlist_h,
                ),
            ansmgr,
            get_nav,
            outfile = args.output
            );

    if dog:
        ndog.nav = dog.nav;

    dog = ndog;
    task = dog._InternalTask(cmd = None, args = args);
    stime = time.time();

    getcookie = gui_getcookie(default = args, attr = "cookies", queue = queue, cb = update_cookie);

    err_handle = unknown_err_handler(queue = queue);

    libdogs.init_hooks(cookie_hook = getcookie, nav_hook = get_nav, logger_hook = logger, err_hook = err_handle);


    try:
        dog.submit(task);
        cleanup();

    except KeyboardInterrupt:
        cleanup();

    except BaseException as err:
        cleanup();
        raise err;

    argv = list(argv);
    for ia,ag in enumerate(argv.copy()):
        if ag == "--cookies":
            argv[ia+1] = args.cookies;

    return (dog, args, argv);


class RNone:
    def __init__(self):
        pass;

class Scheduler:
    class Group:
        def __init__(self, parser, pkg_name, logger, *argv, **kwargs):
            pass;

    def spawn(self):
        pass;

    def configure(self, *argv):
        pass;




def gui_main(parser, pkg_name, argv = [], kinfo = None):

    import tkinter, tkinter.ttk, tkinter.filedialog
    import queue;


    pkg_name = pathlib.Path(pkg_name);

    pkg_dir = pkg_name if pkg_name.is_dir() else pkg_name.parent;

    #wlist_h = Wlist_Handler(kinfo, lpath = str(pkg_dir.resolve()));


    logger = logging.getLogger('tmadog');

    logger.setLevel(logging.DEBUG);
    # create file handler which logs even debug messages
    dfh = logging.FileHandler(str(pkg_dir.joinpath('debug.log')), mode = "w");
    dfh.setLevel(logging.DEBUG);

    fatal = logging.FileHandler(str(pkg_dir.joinpath('fatal.log')), mode = "w");
    fatal.setLevel(logging.CRITICAL);

    stdout = logging.StreamHandler();
    stdout.setLevel(logging.INFO);

    dfh.setFormatter(logging.Formatter('%(asctime)s: %(name)s: %(levelname)s: %(message)s'));

    stdout.setFormatter(logging.Formatter('%(name)s: %(levelname)s: %(message)s'));

    # add the handlers to the logger
    logger.addHandler(dfh);
    logger.addHandler(fatal);
    logger.addHandler(stdout);

    stat_tab = {};
    args = None;
    dog = None;
    frame = None;
    rez = None;
    
    stdscr = tkinter.Tk();
    stdscr.geometry(GEOMETRY);
    stdscr.title("TMADOG version %s" % (VERSION,));
    s_gran = 120 if stdscr.tk.call('tk', 'windowingsystem').startswith("win") else 1;

    argv_frame = tkinter.Frame(stdscr);
    argv_frame.place(x = 0, y = 0, relwidth = 1, relheight = 1/3);
    
    sig = tkinter.StringVar();
    tqueue = dog_idl.PQueue();
    objs = [];

    #def runner():
    #    nonlocal rez, argv, dog, args;
    #    rez = gui_start(parser, pkg_name, logger, *argv, dog = dog,
    #            wlist_h = wlist_h, queue = tqueue);
    #    if rez:
    #        dog, args, argv = rez;

    #        stat_tab.update(
    #                mkstat_tab(dog)
    #                );

    #        if stat_tab:
    #            write_stat_raw(stat_tab, args.stats);

    #    sig.set("Done");
    #

    class _XQueue:
        def __call__(self):
            return self.clear_queue();
        
        @property
        def __name__(self):
            return self.clear_queue.__name__;

        def clear_queue(self):
            try:
                task = tqueue.get(block = False);
                if isinstance(task.signum, int) and task.signum >= 0:
                    signum = 0xff & task.signum;
                    if signum < len(objs) and callable(objs[signum]):
                        task.signum = task.signum >> 8;
                        objs[signum](task);
                    else:
                        task();
                else:
                    task();

                tqueue.task_done();
            except queue.Empty:
                pass;
    
            stdscr.after(1000, self.clear_queue);

    ui = factory_gui2argv(argv_frame, parser, *argv);

    objs.append();

    ui.show();

    ready_btn = tkinter.Button(stdscr, text="Run Dog", font =
            tkinter.font.Font(family="Arial", size = 30, weight = "bold"),
            background = "green", state = "normal", command = lambda : print(ui.ready, ui.get_cmdline(), "\n\n"));

    ready_btn.place(rely = 1/3, x = 0, relheight = 1/8, relwidth = 1);

    dashpad = tkinter.Frame(stdscr);
    dashpad.place(x = 0, rely = 1/3 + 1/8, relheight = 1 - (1/3 + 1/8), relwidth = 1);

    dashboard = dog_idl.Dashboard(dashpad, s_gran, pqueue = tqueue, signum = len(objs), sigbits = 8);

    objs.append(dashboard);
    dashboard.show();

    #stdscr.after(5000, _XQueue());


    stdscr.mainloop();

    #while True:
    #    if frame:
    #        frame.destroy();
    #    argv, frame = factory_gui2argv(stdscr, parser, *argv);
    #    if not argv:
    #        break;
    #    
    #    th = threading.Thread(target = runner, daemon = True);
    #    th.start();
    #    stdscr.wait_variable(sig); 

    #stdscr.destroy();




if __name__ == '__main__':

    pkg_name = pathlib.Path(sys.argv[0]);

    pkg_dir = pkg_name if pkg_name.is_dir() else pkg_name.parent;

    parser = libdogs.DogCmdParser (fromfile_prefix_chars='@');

    parser.add_argument ('--matno', help = 'Your Matric Number', nargs = "+",
            action = libdogs.AppendList, dest = libdogs.P_USR, required = True);

    parser.add_argument ('--pwd', help = 'Your password', nargs = "+", action =
            libdogs.AppendList, dest = libdogs.P_PWD, required = True);

    parser.add_argument ('--crscode', help = 'Your target course', nargs = "+",
            action = libdogs.AppendList, dest = libdogs.P_CRSCODE);

    parser.add_argument ('--tma', nargs = "+", help = 'Your target TMA for the chosen course',
            action = libdogs.AppendList, dest = libdogs.P_TMA, type = int,
            required = True);

    parser.add_argument ('--config', help = 'configuration file to use', dest = libdogs.P_WMAP);

    parser.add_argument ('--debug', action = 'store_true', help = 'To enable debug mode')

    parser.add_argument ('--qstdump', default = 'dumpqst.json', help = 'The dump file for questions')

    parser.add_argument ('--database', '-db', default =
            str(pkg_dir.joinpath("noudb")), help = 'The database to use')

    parser.add_argument ('--noupdatedb', '-nodb', action = 'store_false', dest = 'updatedb', default = True, help = 'Update the database in use')

    parser.add_argument ('--url', help = 'The remote url if no local server', action = libdogs.AppendList, required = True, dest = libdogs.P_URL)


    parser.add_argument ('--cookies', help = 'Website cookies');

    parser.add_argument ('--output', help = "output file format",
            default = str(pkg_dir.joinpath("output/{matno}_{crscode}_TMA{tmano}.txt")));

    parser.add_argument ('--stats', '--summary', help = 'where to write a summary of a run to', dest = "stats"
        , default = str(pkg_dir.joinpath("dog.stat.txt")));

    parser.add_argument ('--page-cache', help = 'where to write cached pages',
            dest = "cache", default = str(pkg_dir.joinpath("dog_cache")));

    parser.add_argument("--overwrite", action = "store_true", help = "always update cached pages");

    parser.add_argument("--cache-first", action = "store_true",
            help = "check cached pages before any remote request for the page - not all cached pages will be used.");

    parser.add_argument("--exclude", action = libdogs.AppendList, help =
            "course codes to exclude e.g for NOUN students GST", nargs = "+");

    qk_psr = argparse.ArgumentParser();

    qk_psr.add_argument("--no-gui", action = "store_const", const = main,
            default = gui_main, dest = "main");


    args, rest = qk_psr.parse_known_args(sys.argv);

    if str(pkg_name) == rest[0]:
        rest.pop(0);

    #r = -1;

    #while True:
    #    r = checks(pkg_name, retry = True if r != -1 else False);

    #    if r == CHK_QUIT:
    #        sys.exit(1);
    #    elif isinstance(r, CHK_SUCCESS):
    #        break;


    try:
        args.main(parser, pkg_name, rest);

    except ModuleNotFoundError:
        main(parser, pkg_name, rest);

    except BaseException as err:
        import traceback
        print (err, "\n\n");
        traceback.print_tb(err.__traceback__);
        time.sleep(10);

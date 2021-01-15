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

VERSION = 1.00;
GEOMETRY = '400x400+100+100';

CANONICAL_URL = "https://www.nouonline.net";

CHK_QUIT = False;
CHK_FAIL = None;
CHK_SUCCESS = True;

def getkey(retry = False):
    
    user_key = None;
    ts = None;
    win = None;
    ret = CHK_FAIL;
    msg = "Please input your key" if not retry else "Invalid or expired key.  Please try again.";

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

        dropbox.libdogs.init_hooks(err_hook = unknown_err_handler);

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

    if win:
        win.destroy();

    if not ts:
        return ret;

    return (user_key, ts);


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

def checks(pkg_name, retry = False):
    pkg_dir = pathlib.Path(pkg_name).parent;

    keyf = pkg_dir.joinpath(".dogger");

    if not keyf.exists():
        kt = getkey(retry);

        if not kt:
            return kt;

        key, tstamp = kt;
        kfile = pkg_dir.joinpath("." + str(key));
        kfile.write_text(str(tstamp));
        write_keyfile(str(keyf), "%s|%s|%s" % (str(kfile.resolve()), tstamp, uuid.getnode()));
        return True;

    else:
        ret = CHK_SUCCESS;
        st = read_keyfile(str(keyf));
        
        try:
            kfile,tstamp,mac = st.split("|");
        except TypeError:
            print("invalid key file");
            return CHK_QUIT;

        #NOTE: MAC ain't reliable
        #if not hasattr(sys, "getandroidapilevel"):
        #  ret = str(uuid.getnode()) == mac;
        kfile = pathlib.Path(kfile);
        return ret and kfile.exists() and libdogs.read_file_text(str(kfile)) == tstamp;


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
        fp.write(ok_str);
        fp.write(not_ok_str);
        fp.write(sta);

    return crsreg;

def main (parser, pkg_name, argv):

    pkg_name = pathlib.Path(pkg_name);

    pkg_dir = pkg_name if pkg_name.is_dir() else pkg_name.parent;

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

    argv, rest = collapse_file_argv(parser, argv);
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
    mstr = libdogs.read_file_text(getattr(args, libdogs.P_WMAP));
    mp.read_string (mstr);

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


def gui_get_argv(scr, parser, *pargs):

    import tkinter, tkinter.ttk, tkinter.filedialog, tkinter.font

    psr = libdogs.DogCmdParser ();

    psr.add_argument ('--matno', nargs = "+", action = libdogs.AppendList);

    psr.add_argument ('--pwd', nargs = "+", action = libdogs.AppendList);

    psr.add_argument ('--crscode', nargs = "+", action = libdogs.AppendList, type = str, default = "all");

    psr.add_argument ('--tma', nargs = "+", action = libdogs.AppendList, type = str, default = "1");

    psr.add_argument ('--url', default = "https://www.nouonline.net");

    psr.add_argument ('--cookies', help = 'Website cookies');

    arr = [];

    ready = ARG_INCOMPLETE;

    ready_btn = tkinter.Button(scr, text="Run Dog", font = tkinter.font.Font(family="Arial", size = 40, weight = "bold"));

    ready_btn["state"] = "disabled";

    def check(pro, v = None):
        nonlocal arr, ready, ready_btn, scr;
        v = pro["val"].get() if v == None else v;

        if not v or v == pro.get("hint", ""):
            ready_btn["state"] = "disabled";
            return;

        if arr:
            for a in arr:
                if a is pro:
                    continue;

                v = a["val"].get();
                if v == a.get("hint", ""):
                    ready_btn["state"] = "disabled";
                    return;

            ready_btn["state"] = "normal";


    def nop():
        nonlocal ready, scr;
        ready = ARG_QUIT;
        scr.destroy();

    args, rest = psr.parse_known_args(pargs);
    
    argv_frame = tkinter.ttk.Frame(scr);
    argv_frame.place(x = 0, y = 0, relheight = 3/4, relwidth = 1);

    url = {
            "def": args.url,
            "val": tkinter.StringVar(value = args.url),
            "name": "WEBSITE"
            };

    url["wgt"] = tkinter.Entry(argv_frame, textvariable = url["val"], validate =
            "key", validatecommand = (scr.register(validate_entry(url, check)), '%P'));
    #url["wgt"].bind("<FocusIn>", unhint(url));
    url["wgt"].bind("<FocusOut>", lambda e: url["val"].set(url["def"]) if not
            url["val"].get() else None);

    cookies = {
            "hint": "file downloaded from a browser",
            "val": tkinter.StringVar(),
            "name": "COOKIE FILE",
            "ign_hint": False
            };

    cookies["val"].set(cookies["hint"] if not args.cookies else args.cookies);

    cookies["wgt"] = tkinter.Entry(argv_frame, textvariable = cookies["val"], validate = "key", validatecommand = (scr.register(validate_entry(cookies)), '%P'));
    #cookies["wgt"].bind("<FocusOut>", hinter(cookies, check));
    cookies["wgt"].bind("<FocusIn>", gf(cookies, scr, check));

    tma = {
            "def": args.tma,
            "val": tkinter.StringVar(value = args.tma),
            "name": "TMA"
            };

    tma["wgt"] = tkinter.Spinbox(argv_frame, **{"from": 1}, to = 3, textvariable = tma["val"]); 

    arr.extend([url, cookies, tma]);
    
    if not args.matno or args.pwd:
        f_args = {
                "def": None,
                "val": tkinter.StringVar(),
                "name": "TMAFILE",
                "hint": "File containing matric numbers and passwords",
                "ign_hint": False,
                };

        f_args["val"].set(f_args["hint"]);

        f_args["wgt"] = tkinter.Entry(argv_frame, textvariable =
                f_args["val"], validate = "key", validatecommand =
                (scr.register(validate_entry(f_args)), '%P'));
        #f_args["wgt"].bind("<FocusOut>", hinter(cookies));
        f_args["wgt"].bind("<FocusIn>", gf(f_args, scr, check));

        for ia, arg in enumerate(rest):
            if parser.fromfile_prefix_chars and arg.startswith(parser.fromfile_prefix_chars):
                f_args["def"] = rest.pop(ia)[1:];
                f_args["val"].set(f_args["def"]);
                break;

        arr.append(f_args);

    alen = len(arr);

    for ia, ar in enumerate(arr):
        tkinter.Label(argv_frame, text = ar["name"], justify = tkinter.LEFT).place(relx = 0, rely = ia/alen,
                relwidth = 1/4);
        ar["wgt"].place(relx = 1/4, rely = ia/alen, relwidth = 3/4);


    def _ready():
        argstr = "--url %s --cookies %s --tma %s" 
        scr.destroy();
       


    scr.protocol("WM_DELETE_WINDOW", nop);


    ready_btn["state"] = "normal" if ready else "disabled";
    ready_btn["command"] = _ready;
    ready_btn.place(relheight = 1/4, rely = 3/4, x = 0, relwidth = 1);


    scr.mainloop();

    return ARG_INCOMPLETE;
    if not ready:
        return ready;


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


def gui_getcookie(default = None, attr = None, cb = None):

    import tkinter.messagebox, tkinter.filedialog

    def _getcookie(nav):
        res = tkinter.messagebox.askyesnocancel(title = "Cookie File",
                icon = "question", message = "Cookies needed. Do you want to use a different file", detail = "click yes to choose a file, click no to use previous file. click cancel to exit the program");
        
        if res == None:
            raise KeyboardInterrupt();

        if res:
            res = tkinter.filedialog.askopenfilename(title = "Cookie File");

        if not res:
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


def unknown_err_handler(err, *pargs):
    import tkinter.messagebox, tkinter.filedialog

    res = tkinter.messagebox.askretrycancel(title = "Error",
            icon = "error", message = "An error occured", detail = "%s" % (err,));


    if res:
        return status.Status(status.S_OK, "continue action", err);
    else:
        raise KeyboardInterrupt();


def collapse_file_argv(parser, argv):
    aid = parser.fromfile_prefix_chars;
    if not aid:
        return [];
    
    arg_res = [];
    rest = [];

    for arg in argv:
        if not isinstance(arg, str) or not arg.startswith(aid):
            rest.append(arg);
            continue;

        args = libdogs.read_file_text(arg[1:]);
        for arg_line in args.split("\n"):
            if not re.match(r'^\s*#.*', arg_line):
                arg_res.extend(arg_line.split());

    return (arg_res, rest);


def gui_start(parser, pkg_name, logger, argr):
    pkg_name = pathlib.Path(pkg_name);

    pkg_dir = pkg_name if pkg_name.is_dir() else pkg_name.parent;

    logger.info("Welcome to TMADOG version %s\n" % (VERSION,));
    
    aid = parser.fromfile_prefix_chars if parser.fromfile_prefix_chars else "";

    argr = ["--cookie", argr[0], "%s%s" % (aid,argr[1])];
    argv = argr.copy();
    argv, rest = collapse_file_argv(parser, argv);
    argv.extend(rest);

    args,ex = parser.parse_known_args(argv);


    def get_nav(cli):
        nonlocal dog, getcookie;
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


    def update_cookie(f):
        nonlocal args;
        args.cookies = f;


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

    dog = simple_dog.SimpleDog(
            libdogs.preprocess(
                args,
                args.exclude if args.exclude else [], # NOTE defaults like
                # this should be in config
                ),
            ansmgr,
            get_nav,
            outfile = args.output
            );

    task = dog._InternalTask(cmd = None, args = args);
    stime = time.time();
        
    getcookie = gui_getcookie(default = args, attr = "cookies", cb = update_cookie);
    
    err_handle = unknown_err_handler;

    libdogs.init_hooks(cookie_hook = getcookie, nav_hook = get_nav, logger_hook = logger, err_hook = err_handle);

    logger.debug("initializing answer manager");

    try:
        dog.submit(task);
        cleanup();

    except KeyboardInterrupt:
        cleanup();

    except BaseException as err:
        cleanup();
        raise err;

    return ("--cookie", args.cookies, argr[-1]);


def gui_main(parser, pkg_name, argv = []):

    import tkinter, tkinter.ttk, tkinter.filedialog


    pkg_name = pathlib.Path(pkg_name);

    pkg_dir = pkg_name if pkg_name.is_dir() else pkg_name.parent;

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



    while True:
        stdscr = tkinter.Tk();
        stdscr.geometry(GEOMETRY);
        stdscr.title("TMADOG version %s" % (VERSION,));
        argv = gui_get_argv(stdscr, parser, *argv);
        if not argv:
            return None;

        sec = tkinter.Tk();
        sec.withdraw();
        argv = gui_start(parser, pkg_name, logger, argv);
        sec.destroy();





if __name__ == '__main__':

    if time.time() >= 1612137600: # for february 1st.
        print("Please renew your package as the current package has expired");
        sys.exit(1);

    parser = libdogs.DogCmdParser (fromfile_prefix_chars='@');

    parser.add_argument ('--matno', help = 'Your Matric Number', nargs = "+",
            action = libdogs.AppendList, dest = libdogs.P_USR, required = True);

    parser.add_argument ('--pwd', help = 'Your password', nargs = "+", action =
            libdogs.AppendList, dest = libdogs.P_PWD, required = True);

    parser.add_argument ('--crscode', help = 'Your target course', nargs = "+",
            action = libdogs.AppendList, dest = libdogs.P_CRSCODE, required =
            True);

    parser.add_argument ('--tma', nargs = "+", help = 'Your target TMA for the chosen course',
            action = libdogs.AppendList, dest = libdogs.P_TMA, type = int,
            required = True);

    parser.add_argument ('--config', help = 'configuration file to use', dest = libdogs.P_WMAP);

    parser.add_argument ('--debug', action = 'store_true', help = 'To enable debug mode')

    parser.add_argument ('--qstdump', default = 'dumpqst.json', help = 'The dump file for questions')

    parser.add_argument ('--database', '-db', help = 'The database to use')

    parser.add_argument ('--noupdatedb', '-nodb', action = 'store_false', dest = 'updatedb', default = True, help = 'Update the database in use')

    parser.add_argument ('--url', help = 'The remote url if no local server', action = libdogs.AppendList, required = True, dest = libdogs.P_URL)


    parser.add_argument ('--cookies', help = 'Website cookies');

    parser.add_argument ('--output', help = "output file format");

    parser.add_argument ('--stats', '--summary', help = 'where to write a summary of a run to', dest = "stats");

    parser.add_argument ('--page-cache', help = 'where to write cached pages',
            dest = "cache");

    parser.add_argument("--overwrite", action = "store_true", help = "always update cached pages");

    parser.add_argument("--cache-first", action = "store_true",
            help = "check cached pages before any remote request for the page - not all cached pages will be used.");

    parser.add_argument("--exclude", action = libdogs.AppendList, help =
            "course codes to exclude e.g for NOUN students GST", nargs = "+");

    qk_psr = argparse.ArgumentParser();
    
    qk_psr.add_argument("--no-gui", action = "store_const", const = main,
            default = gui_main, dest = "main");

    pkg_path = sys.argv[0];

    args, rest = qk_psr.parse_known_args(sys.argv);
   
    if pkg_path == rest[0]:
        rest.pop(0);
    
    r = -1;

    while True:
        r = checks(pkg_path, retry = True if r != -1 else False);

        if r == CHK_QUIT:
            sys.exit(1);
        elif r == CHK_SUCCESS:
            break;


    try:
        args.main(parser, pkg_path, rest);

    except ModuleNotFoundError:
        main(parser, pkg_path, rest);

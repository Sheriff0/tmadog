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


VERSION = 1.00;

def check(pkg_name):
    import uuid
    import hashlib
    import locale
    import os
    import sys

    pkg_dir = pathlib.Path(os.sep.join(str(pathlib.Path(pkg_name).resolve()).split(os.sep)[:-1]));
    mac = bytes(str(uuid.getnode()), encoding = locale.getpreferredencoding());
    hsh = hashlib.sha256(mac);

    fi = pathlib.Path(pkg_dir.joinpath("dog_key.txt"));

    if not fi.exists():
        print("You don't have the required key to use this product.");
        return False;

    else:
        with open(str(fi), "r") as f:
            byt = f.read();
            return byt == hsh.hexdigest();


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


def gui_get_argv(scr, f_cookie = None, f_arg = None):

    import tkinter, tkinter.ttk, tkinter.filedialog

    ready = False;
    argv_frame = tkinter.ttk.Frame(scr, takefocus = 1);

    ff_cookie = tkinter.StringVar();

    ff_arg = tkinter.StringVar();

    ff_cookie.set("No file" if not f_cookie else f_cookie);

    ff_arg.set("No file" if not f_arg else f_arg);

    def nop():
        nonlocal ready, scr;
        ready = None;
        scr.destroy();


    def _set_cookie_f(fp):
        nonlocal f_cookie, ff_cookie, ready_btn;
        if fp:
            f_cookie = fp;
            ff_cookie.set(fp);

        if f_cookie and f_arg:
            ready_btn["state"] = "normal";


    def _set_arg_f(fp):
        nonlocal f_arg, ff_arg, ready_btn;
        if fp:
            f_arg = fp;
            ff_arg.set(fp);

        if f_cookie and f_arg:
            ready_btn["state"] = "normal";


    def _ready():
        nonlocal ready, f_arg, f_cookie, scr;

        #argv_frame.destroy();
        ready = (f_cookie, f_arg)
        scr.destroy();
       

    scr.protocol("WM_DELETE_WINDOW", nop);

    c_btn_txt = "Get cookies";

    cookie_btn = tkinter.ttk.Button(argv_frame, text=c_btn_txt, command = gui_getfile(_set_cookie_f, "Cookie file"));

    label_cookie = tkinter.ttk.Label(argv_frame, textvariable = ff_cookie);

    arg_f_txt = "Get TMA file";

    arg_btn = tkinter.ttk.Button(argv_frame, text=arg_f_txt, command = gui_getfile(_set_arg_f, "TMA file"));

    label_arg = tkinter.ttk.Label(argv_frame, textvariable = ff_arg);

    ready_btn = tkinter.ttk.Button(argv_frame, text="Run Dog", command = _ready);

    ready_btn["state"] = "normal" if f_cookie and f_arg else "disabled";

    argv_frame.grid(column=0, row=0, sticky=(tkinter.N, tkinter.W, tkinter.E, tkinter.S));

    for child in argv_frame.winfo_children():
        child.pack(fill = tkinter.X, expand = True, side = tkinter.TOP, pady = 10);


    scr.mainloop();
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
        res = tkinter.messagebox.askyesno(title = "Cookie File",
                icon = "question", message = "Cookies needed. Update cookie file", detail = "click yes to choose a file, no to use previous file");

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
        return status.Status(status.S_OK, "continue action", cause);
    else:
        raise KeyboardInterrupt();


def gui_start(parser, pkg_name, logger, argv):
    pkg_name = pathlib.Path(pkg_name);

    pkg_dir = pkg_name if pkg_name.is_dir() else pkg_name.parent;

    logger.info("Welcome to TMADOG version %s\n" % (VERSION,));

    argv = ["--cookie", argv[0], "@%s" % (argv[1],)];

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
        stdscr.geometry('300x200+100+100');
        stdscr.title("TMADOG version %s" % (VERSION,));
        argv = gui_get_argv(stdscr, *argv);
        if not argv:
            return None;

        gui_start(parser, pkg_name, logger, argv);





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

    args.main(parser, pkg_path, rest);

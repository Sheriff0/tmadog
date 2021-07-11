class RNone:
    def __init__(self):
        pass;


import tkinter.messagebox

class XScheduler:
    class Group:
        def __init__(self, parser, pkg_name, logger, *argv, **kwargs):
            pass;

    def __init__(self, logger, reporter):
        self.reporter = reporter;
        self.logger = logger;
    
    def holla(self):
        return tkinter.messagebox.showinfo(title = "World", message = "Hello, World!", detail = "xxx");

    def para(self):
        return tkinter.messagebox.showinfo(title = "Para",
                message = "I just want attention!", detail = "xxx");

    def runner(self, argv):
        self.logger.alloc();
        self.logger.logger.info("got %s" % (argv));
        err = math.trunc(random.random() * 100)
        self.logger.append_reporter(
                dog_idl.Resolver(
                    ["hello"],
                    [self.holla],
                    )
                );
        res = dog_idl.Reporter(100);
        self.logger.append_reporter(res);
        for a in range(100):
            time.sleep(3);
            self.logger.logger.info("I just did %s out of 100" % (a,));
            res.progress(a);

    def configure(self, argv):
        threading.Thread(target = self.runner, args = (argv,), daemon = True).start(); 



class Scheduler:
    class Group:
        def __init__(self, parser, pkg_name, logger, *argv, **kwargs):
            pass;

    def __init__(self, logger, resolver, reporter):
        self.reporter = reporter;
        self.logger = logger;
        self.resolver = resolver;
        self.navs = {};
    
    # NOTE Refactor
    def register_error(self, keys, commands, aid = None):
        # return a task for the caller to wait on for resolution
        aid = threading.get_ident() if not aid else aid;
        task = Task(None);
        act = self.get_activity(aid);
        cb = Task(self.de_register_error, aid);
        act.register.put(
                Resolver(
                    self.resolution_scr,
                    keys,
                    commands,
                    task,
                    cb
                    ),
                );
        
        return task;

    def register_progress(self, cur, total, aid = None):
        aid = threading.get_ident() if not aid else aid;
        act = self.get_activity(aid);
        if not act:
            return False;

        if not act.reporters:
            act.reporters.append(Reporter(self.status_scr, total));
            if self.get_vid_of(aid) == self.id:
                act.reporters.place();

        act.reporters.progress(cur);


    def configure(parser, pkg_name, argv, kinfo = None):

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





def gui_main(parser, pkg_name, argv = [], kinfo = None):

    import tkinter, tkinter.ttk, tkinter.filedialog
    import queue;
    
    AFTER_MS = 100;

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

    logger.info("initializing a cookie client, please make sure a server is installed on your browser");
    cookie_client = c_server.DogCookieClient(
            (c_server.DEFAULT_HOST, c_server.DEFAULT_PORT),
            c_server.RequestHandler
            );   
   
    threading.Thread(target = cookie_client.serve_forever, daemon = True).start();

    libdogs.init_hooks(cookie_client = cookie_client);

    stat_tab = {};
    args = None;
    dog = None;
    frame = None;

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
    
            stdscr.after(AFTER_MS, self.clear_queue);

    ui = factory_gui2argv(argv_frame, parser, *argv);

    objs.append(ui);

    while True:
        if frame:
            frame.destroy();
        argv, frame = gui_get_argv(stdscr, parser, *argv);
        if not argv:
            break;

    dashpad = tkinter.Frame(stdscr);
    dashpad.place(x = 0, rely = 1/3 + 1/8, relheight = 1 - (1/3 + 1/8), relwidth = 1);

    dashboard = dog_idl.Dashboard(dashpad, s_gran, pqueue = tqueue, signum = len(objs), sigbits = 8, mlogger = logger);

    objs.append(dashboard);
    dashboard.show();
    
    sch = XScheduler(dashboard, dashboard);

    ready_btn = tkinter.Button(stdscr, text="Run Dog", font =
            tkinter.font.Font(family="Arial", size = 30, weight = "bold"),
            background = "green", state = "normal", command = lambda : sch.configure(ui.get_argv()));

    ready_btn.place(rely = 1/3, x = 0, relheight = 1/8, relwidth = 1);

    stdscr.after(AFTER_MS, _XQueue());


    stdscr.mainloop();

            if stat_tab:
                write_stat_raw(stat_tab, args.stats);

    stdscr.destroy();
    cookie_client.shutdown();
import dog_idl
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






class RNone:
    def __init__(self):
        pass;


import tkinter.messagebox

class XScheduler:
    class Group:
        def __init__(self, parser, pkg_name, logger, *argv, **kwargs):
            pass;

    def __init__(self, logger, reporter):
        self.reporter = reporter;
        self.logger = logger;
    
    def holla(self):
        return tkinter.messagebox.showinfo(title = "World", message = "Hello, World!", detail = "xxx");

    def para(self):
        return tkinter.messagebox.showinfo(title = "Para",
                message = "I just want attention!", detail = "xxx");

    def runner(self, argv):
        self.logger.alloc();
        self.logger.logger.info("got %s" % (argv));
        err = math.trunc(random.random() * 100)
        self.logger.append_reporter(
                dog_idl.Resolver(
                    ["hello"],
                    [self.holla],
                    )
                );
        res = dog_idl.Reporter(100);
        self.logger.append_reporter(res);
        for a in range(100):
            time.sleep(3);
            self.logger.logger.info("I just did %s out of 100" % (a,));
            res.progress(a);

    def configure(self, argv):
        threading.Thread(target = self.runner, args = (argv,), daemon = True).start(); 



class Scheduler:
    class Group:
        def __init__(self, parser, pkg_name, logger, *argv, **kwargs):
            pass;

    def __init__(self, logger, resolver, reporter):
        self.reporter = reporter;
        self.logger = logger;
        self.resolver = resolver;
        self.navs = {};
    
    # NOTE Refactor
    def register_error(self, keys, commands, aid = None):
        # return a task for the caller to wait on for resolution
        aid = threading.get_ident() if not aid else aid;
        task = Task(None);
        act = self.get_activity(aid);
        cb = Task(self.de_register_error, aid);
        act.register.put(
                Resolver(
                    self.resolution_scr,
                    keys,
                    commands,
                    task,
                    cb
                    ),
                );
        
        return task;

    def register_progress(self, cur, total, aid = None):
        aid = threading.get_ident() if not aid else aid;
        act = self.get_activity(aid);
        if not act:
            return False;

        if not act.reporters:
            act.reporters.append(Reporter(self.status_scr, total));
            if self.get_vid_of(aid) == self.id:
                act.reporters.place();

        act.reporters.progress(cur);


    def configure(parser, pkg_name, argv, kinfo = None):

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





def gui_main(parser, pkg_name, argv = [], kinfo = None):

    import tkinter, tkinter.ttk, tkinter.filedialog
    import queue;
    
    AFTER_MS = 100;

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
    
            stdscr.after(AFTER_MS, self.clear_queue);

    ui = factory_gui2argv(argv_frame, parser, *argv);

    objs.append(ui);

    ui.show();

    dashpad = tkinter.Frame(stdscr);
    dashpad.place(x = 0, rely = 1/3 + 1/8, relheight = 1 - (1/3 + 1/8), relwidth = 1);

    dashboard = dog_idl.Dashboard(dashpad, s_gran, pqueue = tqueue, signum = len(objs), sigbits = 8, mlogger = logger);

    objs.append(dashboard);
    dashboard.show();
    
    sch = XScheduler(dashboard, dashboard);

    ready_btn = tkinter.Button(stdscr, text="Run Dog", font =
            tkinter.font.Font(family="Arial", size = 30, weight = "bold"),
            background = "green", state = "normal", command = lambda : sch.configure(ui.get_argv()));

    ready_btn.place(rely = 1/3, x = 0, relheight = 1/8, relwidth = 1);

    stdscr.after(AFTER_MS, _XQueue());


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



class SimpleDog:

    def __init__ (self, usrs, amgr, get_nav, outfile = None, **req_args):
        self.arg_gens = [];
        self.prep_argv = [];
        self.prep_argc = 0;
        self.status = status.Status();
        self.ctrl = DOG_CTRL_RUN_WAIT;
        self.ctrl_lock = threading.Lock();
        self.tasktab = [];
        self.tasktab_size = 0;
        self.amgr = amgr;
        self.usrs = usrs;
        self.nav = None;
        self.get_nav = get_nav;
        self.outfile = outfile;
        self.exit_cb = exit_cb;
    
    def run_wait(self):
        self.ctrl_lock.acquire();
        self.ctrl = DOG_CTRL_RUN_WAIT;
        self.ctrl_lock.release();

        while self.ctrl != DOG_CTRL_RUNNABLE:
            pass;

    def pause_wait(self):
        self.ctrl_lock.acquire();
        self.ctrl = DOG_CTRL_PAUSE_WAIT;
        self.ctrl_lock.release();
        while self.ctrl != DOG_CTRL_PAUSE:
            pass;

    def wait_for(self, flag = DOG_CTRL_RUNNABLE):
        while self.ctrl != flag:
            if self.ctrl == DOG_CTRL_RUN_WAIT:
                self.ctrl_lock.acquire();
                self.ctrl = DOG_CTRL_RUNNABLE;
                self.ctrl_lock.release();

            elif self.ctrl == DOG_CTRL_PAUSE_WAIT:
                self.ctrl_lock.acquire();
                self.ctrl = DOG_CTRL_PAUSE;
                self.ctrl_lock.release();

            elif self.ctrl == DOG_CTRL_STOP_WAIT:
                # lock it forever.
                self.ctrl_lock.acquire();
                self.ctrl = DOG_CTRL_STOP;
                if callable(self.exit_cb):
                    self.exit_cb();

                sys.exit(0);

    def stop_wait(self):
        self.ctrl_lock.acquire();
        self.ctrl = DOG_CTRL_STOP_WAIT;
        self.ctrl_lock.release();

        while self.ctrl != DOG_CTRL_STOP:
            pass;

    def _alloc(self, task = None):
        self.tasktab.append(task);
        self.tasktab_size += 1;

    def argv(self):
        """iterate over all arguments - raw and preprocessed.
        unlike the getarg_by_* functions that skip statuses, if a preprocessor returns a status
        instead of a valid argument that status is yielded too(but not appended
        to .prep_argv).
        """
        for arg in self.prep_argv:
            yield arg;

        for arg in self.usrs:
            self.prep_argv.append(
                        arg,
                    );
            self.prep_argc += 1;

            yield arg;


    def getarg_by_index(self, idx = 0):
        if not idx >= self.prep_argc:
            return idx;

        i = prep_argc - 1;

        for arg in self.usrs:
            self.prep_argv.append(
                        arg,
                    );
            self.prep_argc += 1;

            if i == idx:
                return idx;
            i+=1;

        return None;

    def getarg_by_attr(self, attr, val):
        try:
            return self.prep_argv.index(val, attr);
        except ValueError:
            for arg in self.usrs:
                self.prep_argv.append(
                        arg,
                        );
                self.prep_argc += 1;

                try:
                    i = scrm.QScrList(arg).index(value, attr);
                    return self.prep_argc - 1;
                except ValueError:
                    pass

            return None;

    def submit(self, task):
        if not hasattr(task, "magic") or (task.magic != SUB_MBR or task.magic != SUB_LDR):
            task = self._InternalTask(cmd = self.submit_pre_exec, args = task.args,
                   magic = SUB_LDR);

        ## to keep kick-start schedule pre-execution
        return self.submit_pre_exec(task);

    def submit_pre_exec(self, task):
        #NOTE: remove this... no more pre-execs
        """pre-executor for the submit command.
        pre-execution
        =============
            pre-execution is executing a task before puting it into the
            tasklist. This is to enable a more faster execution of commands that
            create and execute multiple sub-tasks - instead of creating multiple
            tasks and wait for each to call you from the tasklist, you create and
            execute, then send to the list as a last step. this is also useful for
            command whose argument pre-processing invloves remote i/o operations.
        """

        ldr = None;
        mbr = None;

        if task.magic == SUB_LDR:
            ldr = task;
            mbr = task.nxt;
        elif task.magic == SUB_MBR:
            ldr = task.group;
            mbr = task;
        else:
            self.status = status.Status(status.S_ERROR, task);
            return self.status;

        if not mbr:
            # do create and do all members recursively if necessary
            if ldr.nxt:
                # members are already created - execute assuming they are in the
                # task list
                while ldr.nxt:
                    # execute
                    st = self.submit_main(ldr.nxt.args);
                    if st.code == status.S_FATAL or st.code == status.S_ERROR:
                        ldr.nxt.state = tasker.TS_TERM;
                    elif st.code == status.S_INT:
                        ldr.nxt.cmd = self.submit_pre_exec;
                        ldr.nxt.state = tasker.TS_STOPED;
                    else:
                        ldr.nxt.state = tasker.TS_EXITED;

                    ldr.nxt.status = st;
                    self.status = st;
                    ldr = ldr.nxt;
            else:
                self._alloc(ldr);
                # create them and pre_execute them
                prev = ldr;

                for arg in self.argv():
                    if isinstance(arg, status.Status):
                        self._alloc(self._InternalTask(magic = SUB_MBR, group =
                            ldr, cmd = self.nop, args = arg.cause, status = arg,
                            state = tasker.TS_TERM));

                        continue;

                    elif not libdogs.is_net_valid_arg(ldr.args, arg):
                        continue;

                    mbr = self._InternalTask(magic = SUB_MBR, group = ldr, cmd =
                                self.nop, args = arg, status = status.Status());
                    # start submiting
                    st = self.submit_main(arg);
                    if st.code == status.S_FATAL or st.code == status.S_ERROR:
                        mbr.state = tasker.TS_TERM;
                    elif st.code == status.S_INT:
                        mbr.cmd = self.submit_pre_exec;
                        mbr.state = tasker.TS_STOPED;
                    else:
                        mbr.state = tasker.TS_EXITED;

                    mbr.status = st;
                    self._alloc(mbr);
                    self.status = st;
                    prev.nxt = mbr;
                    prev = mbr;

        else:
            # do the member only
            st = self.submit_main(mbr.args);
            if st.code == status.S_FATAL or st.code == status.S_ERROR:
                mbr.state = tasker.TS_TERM;
            elif st.code == status.S_INT:
                mbr.cmd = self.submit_pre_exec;
                mbr.state = tasker.TS_STOPED;
            else:
                mbr.state = tasker.TS_EXITED;

            mbr.status = st;
            self.status = st;

        return self.status;

    def resume_suspended(self):
        for task in self.tasktab:
            if task.state != tasker.TS_STOPED:
                continue;

            st = self.submit_main(task.args);
            if st.code == status.S_FATAL or st.code == status.S_ERROR:
                task.state = tasker.TS_TERM;
            elif st.code == status.S_INT:
                task.cmd = self.submit_pre_exec;
                task.state = tasker.TS_STOPED;
            else:
                task.state = tasker.TS_EXITED;

            task.status = st;

    def submit_main(self, arg):

        nav = self.get_nav(arg);
        if not nav:
            return nav;###handle

        fn = None;
        fp = None;

        if self.outfile:
            fn = pathlib.Path(self.outfile.format(
                crscode = arg[libdogs.P_CRSCODE],
                c = arg[libdogs.P_CRSCODE],
                matno = arg[libdogs.P_USR],
                tmano = arg[libdogs.P_TMA]
                ));




        for ftype in libdogs.fetch_all(nav, arg, **self.req_args):
            if not ftype or isinstance(ftype, status.Status):
                st = ftype;
                break;

            if fn and not fp:
                fp = open(str(fn), "a" if fn.exists() else "w");
                line = "%s" % ("=" * len(arg[libdogs.P_CRSCODE]),);
                fp.write("%s\n%s\n%s\n\n" % (line,arg[libdogs.P_CRSCODE],line));

            st = libdogs.brute_submit(arg, nav, ftype, self.amgr, fp = fp,
                    **self.req_args);

            if st == libdogs.SUBMIT_RETRY_FETCH:
                continue;

            elif not st:
                break;

        if not isinstance(st, status.Status):
            st = status.Status(cause = st);
        if fp:
            fp.close();
        return st;

    def nop(self):
        """like nop in x86 assembly"""
        pass;

    class _InternalTask:
        """ instances of this can find themselves in tha tasktab.
            It is meant for use internally by method that want a task object that is ligther, laxer, and more
            customizable than tasker.DTask
            """
        def __init__(self, cmd, magic = 0, tid = 0, args = None, status = None, group = None, nxt = None, state = tasker.TS_RUNNABLE, disp = tasker.TDISP_PUBLIC):
            self.magic = magic
            self.cmd = cmd;
            self.tid = tid;
            ## the global index possible in a task table
            self.aindex = 0;
            self.refcount = 0;
            self.args = args;
            self.status = status;
            self.disp = disp;
            self.state = state;
            # to support linked lists
            self.nxt = nxt;
            # to support group of tasks and fast access to the begining of a linked
            # list. The first item can be the leader and every .nxt from itself and
            # any other .nxt are member
            self.group = group;

DOG_CTRL_STOP = 0
DOG_CTRL_STOP_WAIT = 1;
DOG_CTRL_RUNNABLE = 2;
DOG_CTRL_RUN_WAIT = 3;
DOG_CTRL_PAUSE = 4;
DOG_CTRL_PAUSE_WAIT = 5;

class SimpleDog:

    def __init__ (self, usrs, amgr, get_nav, outfile = None, exit_cb = None):
        self.arg_gens = [];
        self.prep_argv = [];
        self.prep_argc = 0;
        self.status = status.Status();
        self.ctrl = DOG_CTRL_RUNNABLE;
        self.ctrl_lock = threading.Lock();
        self.tasktab = [];
        self.tasktab_size = 0;
        self.amgr = amgr;
        self.usrs = usrs;
        self.nav = None;
        self.get_nav = get_nav;
        self.outfile = outfile;
        self.exit_cb = exit_cb;
    
    def run_wait(self):
        self.ctrl_lock.acquire();
        self.ctrl = DOG_CTRL_RUN_WAIT;
        self.ctrl_lock.release();

        while self.ctrl != DOG_CTRL_RUNNABLE:
            pass;

    def pause_wait(self):
        self.ctrl_lock.acquire();
        self.ctrl = DOG_CTRL_PAUSE_WAIT;
        self.ctrl_lock.release();
        while self.ctrl != DOG_CTRL_PAUSE:
            pass;

    def wait_for(self, flag = DOG_CTRL_RUNNABLE):
        while self.ctrl != flag:
            if self.ctrl == DOG_CTRL_RUN_WAIT:
                self.ctrl_lock.acquire();
                self.ctrl = DOG_CTRL_RUNNABLE;
                self.ctrl_lock.release();

            elif self.ctrl == DOG_CTRL_PAUSE_WAIT:
                self.ctrl_lock.acquire();
                self.ctrl = DOG_CTRL_PAUSE;
                self.ctrl_lock.release();

            elif self.ctrl == DOG_CTRL_STOP_WAIT:
                # lock it forever.
                self.ctrl_lock.acquire();
                self.ctrl = DOG_CTRL_STOP;
                if callable(self.exit_cb):
                    self.exit_cb();

                sys.exit(0);

    def stop_wait(self):
        self.ctrl = DOG_CTRL_STOP_WAIT;

        while self.ctrl != DOG_CTRL_STOP:
            pass;

    def _alloc(self, task = None):
        self.tasktab.append(task);
        self.tasktab_size += 1;

    def argv(self):
        """iterate over all arguments - raw and preprocessed.
        unlike the getarg_by_* functions that skip statuses, if a preprocessor returns a status
        instead of a valid argument that status is yielded too(but not appended
        to .prep_argv).
        """
        for arg in self.prep_argv:
            yield arg;

        for arg in self.usrs:
            self.prep_argv.append(
                        arg,
                    );
            self.prep_argc += 1;

            yield arg;


    def getarg_by_index(self, idx = 0):
        if not idx >= self.prep_argc:
            return idx;

        i = prep_argc - 1;

        for arg in self.usrs:
            self.prep_argv.append(
                        arg,
                    );
            self.prep_argc += 1;

            if i == idx:
                return idx;
            i+=1;

        return None;

    def getarg_by_attr(self, attr, val):
        try:
            return self.prep_argv.index(val, attr);
        except ValueError:
            for arg in self.usrs:
                self.prep_argv.append(
                        arg,
                        );
                self.prep_argc += 1;

                try:
                    i = scrm.QScrList(arg).index(value, attr);
                    return self.prep_argc - 1;
                except ValueError:
                    pass

            return None;

    def submit(self, task):
        if not hasattr(task, "magic") or (task.magic != SUB_MBR or task.magic != SUB_LDR):
            task = self._InternalTask(cmd = self.submit_pre_exec, args = task.args,
                   magic = SUB_LDR);

        ## to keep kick-start schedule pre-execution
        self.wait_for(DOG_CTRL_RUNNABLE);
        return self.submit_pre_exec(task);

    def submit_pre_exec(self, task):
        #NOTE: remove this... no more pre-execs
        """pre-executor for the submit command.
        pre-execution
        =============
            pre-execution is executing a task before puting it into the
            tasklist. This is to enable a more faster execution of commands that
            create and execute multiple sub-tasks - instead of creating multiple
            tasks and wait for each to call you from the tasklist, you create and
            execute, then send to the list as a last step. this is also useful for
            command whose argument pre-processing invloves remote i/o operations.
        """

        ldr = None;
        mbr = None;

        if task.magic == SUB_LDR:
            ldr = task;
            mbr = task.nxt;
        elif task.magic == SUB_MBR:
            ldr = task.group;
            mbr = task;
        else:
            self.status = status.Status(status.S_ERROR, task);
            return self.status;

        if not mbr:
            # do create and do all members recursively if necessary
            if ldr.nxt:
                # members are already created - execute assuming they are in the
                # task list
                while ldr.nxt:
                    # execute
                    self.wait_for(DOG_CTRL_RUNNABLE);
                    st = self.submit_main(ldr.nxt.args);
                    if st.code == status.S_FATAL:
                        ldr.nxt.state = tasker.TS_TERM;
                    elif st.code == status.S_ERROR:
                        ldr.nxt.cmd = self.submit_pre_exec;
                        ldr.nxt.state = tasker.TS_STOPED;
                    elif st:
                        ldr.nxt.state = tasker.TS_EXITED;

                    ldr.nxt.status = st;
                    self.status = st;
                    ldr = ldr.nxt;
            else:
                self._alloc(ldr);
                # create them and pre_execute them
                prev = ldr;

                self.wait_for(DOG_CTRL_RUNNABLE);
                for arg in self.argv():
                    self.wait_for(DOG_CTRL_RUNNABLE);
                    if isinstance(arg, status.Status):
                        self._alloc(self._InternalTask(magic = SUB_MBR, group =
                            ldr, cmd = self.nop, args = arg.cause, status = arg,
                            state = tasker.TS_TERM));

                        continue;

                    elif not libdogs.is_net_valid_arg(ldr.args, arg):
                        continue;

                    mbr = self._InternalTask(magic = SUB_MBR, group = ldr, cmd =
                                self.nop, args = arg, status = status.Status());
                    # start submiting
                    st = self.submit_main(arg);
                    if st.code == status.S_FATAL:
                        mbr.state = tasker.TS_TERM;
                    elif st.code == status.S_ERROR:
                        mbr.cmd = self.submit_pre_exec;
                        mbr.state = tasker.TS_STOPED;
                    elif st:
                        mbr.state = tasker.TS_EXITED;

                    mbr.status = st;
                    self._alloc(mbr);
                    self.status = st;
                    prev.nxt = mbr;
                    prev = mbr;

        else:
            # do the member only
            st = self.submit_main(mbr.args);
            if st.code == status.S_FATAL:
                mbr.state = tasker.TS_TERM;
            elif st.code == status.S_ERROR:
                mbr.cmd = self.submit_pre_exec;
                mbr.state = tasker.TS_STOPED;
            elif st:
                mbr.state = tasker.TS_EXITED;

            mbr.status = st;
            self.status = st;

        return self.status;

    def submit_main(self, arg):

        self.wait_for(DOG_CTRL_RUNNABLE);
        nav = self.get_nav(arg);
        if not nav:
            return nav;###handle

        fn = None;
        fp = None;

        if self.outfile:
            fn = pathlib.Path(self.outfile.format(
                crscode = arg[libdogs.P_CRSCODE],
                c = arg[libdogs.P_CRSCODE],
                matno = arg[libdogs.P_USR],
                tmano = arg[libdogs.P_TMA]
                ));




        for ftype in libdogs.fetch_all(nav, arg):
            if not ftype:
                st = ftype;
                break;

            if fn and not fp:
                fp = open(str(fn), "a" if fn.exists() else "w");
                line = "%s" % ("=" * len(arg[libdogs.P_CRSCODE]),);
                fp.write("%s\n%s\n%s\n\n" % (line,arg[libdogs.P_CRSCODE],line));

            self.wait_for(DOG_CTRL_RUNNABLE);
            st = libdogs.brute_submit(arg, nav, ftype, self.amgr, fp = fp);
            self.wait_for(DOG_CTRL_RUNNABLE);


            if not st:
                break;

        if not isinstance(st, status.Status):
            st = status.Status(cause = st);
        if fp:
            fp.close();
        return st;

    def nop(self):
        """like nop in x86 assembly"""
        pass;

    class _InternalTask:
        """ instances of this can find themselves in tha tasktab.
            It is meant for use internally by method that want a task object that is ligther, laxer, and more
            customizable than tasker.DTask
            """
        def __init__(self, cmd, magic = 0, tid = 0, args = None, status = None, group = None, nxt = None, state = tasker.TS_RUNNABLE, disp = tasker.TDISP_PUBLIC):
            self.magic = magic
            self.cmd = cmd;
            self.tid = tid;
            ## the global index possible in a task table
            self.aindex = 0;
            self.refcount = 0;
            self.args = args;
            self.status = status;
            self.disp = disp;
            self.state = state;
            # to support linked lists
            self.nxt = nxt;
            # to support group of tasks and fast access to the begining of a linked
            # list. The first item can be the leader and every .nxt from itself and
            # any other .nxt are member
            self.group = group;

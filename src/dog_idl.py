"""
======================================
The Dog Interface Description Language
======================================

example
=======
if = {
    "type": IF_FILE_M,
    "count": 5,
    "name": "argument",
    "choices": None,
    "prefix": "@",
    "suffix": None,
    "required": True,
    
    # this is to enable value translation in commandline generation. keys with a
    # boolean-false value are removed from the output commandline

    "pseudos": {
        "from-file": None,
        "everything" "all",
    },
    ## Depending on the type of interface, some checks can be performed on the
    ## user input; e.g checking if a file is non-empty. To customize the check,
    ## assign to a callable that returns True when input checks and False
    ## otherwise.

    "check": True,

    "hint": "Type all your names (5 max)",

    "default": None,
}
"""

import tkinter, tkinter.ttk, tkinter.filedialog, tkinter.font, tkinter.messagebox

IFD_TYPE = "type";
IFD_COUNT = "count";
IFD_NAME = "name";
IFD_CHOICES = "choices";
IFD_PREFIX = "prefix";
IFD_SUFFIX = "suffix"; 
IFD_REQUIRED = "required";
IFD_PSEUDOS = "pseudos";
IFD_CHECK = "check"; 
IFD_HINT = "hint";
IFD_DEFAULT = "default";


IF_FILE = 0;
IF_SPEC_FILE = 1;
IF_OPTIONS = 2;
IF_STRING = 3;

IF_FILE_M = 0 | ord('m');
IF_SPEC_FILE_M = 1 | ord('m');
IF_OPTIONS_M = 2 | ord('m');
IF_STRING_M = 3 | ord('m');


# is this reasonable?
MAX_DEFAULT_SIZE = 1000000

## Abstract Interface Class(AIC)

class IfName(tkinter.Label):
    def __init__(self, name, *pargs, **kwargs):
        self.name = name;
        super().__init__(*pargs, **kwargs);
    def __repr__(self):
        return str(self.name);

    def __str__(self):
        return repr(self);

class Interface:
    
    def __init__(self):
        self.ready = False;
        self.widget = None;
        self.name = Name;
    
    def get_value(self):
        pass;

    def set_value(self):
        pass;

    def disable(self):
        pass;

    def enable(self):
        pass;

    def destroy(self):
        pass;

    def remove(self):
        pass;

    def check(self, value):
        pass;

def validate(iF, custom_val):
    
    def _val(value):
        return bool(custom_val(iF, value));

    return _val;

def get_local_file(iF, win, cb = None):
    import tkinter.filedialog

    def _gf(e):
        #Remove focus from the invoking widget
        win.focus();
        v = tkinter.filedialog.askopenfilename(master = win, title = str(iF.name));

        # there can be no file too. 
        iF.set_value(v if v else "");

        if cb and callable(cb):
            return cb(iF, v);

    return _gf;


## Factory functions for the various interface types

def create_file_if(stdscr, name, default = None, hint = None, check = False,
        def_on_empty = False):
    
    iF = create_string_if(
            stdscr,
            name,
            default = default,
            hint = hint,
            check = check,
            def_on_empty = def_on_empty,
            );

    iF.widget.bind("<FocusIn>", get_local_file(iF, stdscr));

    return iF;


def create_options_if(stdscr, name , options, default = 0, hint = None):
    class _SIF(Interface):
        def __init__(self, widget, var, name = None, ready = False):
        
            self.widget = widget;
            self.ready = ready;
            self.var = var;
            self.name = name;

        def get_value(self):
            return self.var.get();

        def set_value(self, value):
            return self.var.set(str(value));

    opts = [];
    for itm in options:
        opts.append(itm);

    var = tkinter.StringVar();
    
    name_w = IfName(name, stdscr, text = name); #justify = tkinter.LEFT;
    
    widget = tkinter.ttk.Combobox(stdscr, textvariable = var, values = opts, state = "readonly");

    try:
        if not isinstance(default, int) or default >= len(opts):
            default = opts.index(default);

        widget.current(default);
    except (ValueError, IndexError):
        widget.current(0);


    iF = _SIF(widget, var, name_w, True);

    return iF;

def create_string_if(stdscr, name, default = None, hint = None, check = False,
        def_on_empty = False):

    class _SIF(Interface):
        def __init__(self, widget, var, name = None, ready = False):
        
            self.widget = widget;
            self.ready = ready;
            self.var = var;
            self.name = name;

        def get_value(self):
            return self.var.get();

        def set_value(self, value):
            return self.var.set(str(value));

    var = tkinter.StringVar(value = default);
    widget = tkinter.Entry(stdscr, textvariable = var);

    name_w = IfName(name, stdscr, text = name); #justify = tkinter.LEFT;

    iF = _SIF(widget, var, name_w, True if default else False);
    
    if check:
        if not callable(check):
            check = lambda i, val: bool(val);

        widget["validate"] = "key";
        widget["validatecommand"] = (
                stdscr.register(validate(iF, check)),
                '%P'
                );

    if default and def_on_empty:
        # then iF should be always ready
        iF.ready = True;
        widget.bind("<FocusOut>", lambda e: iF.set_value(default) if not
                iF.get_value() else None);

    return iF;

def create_file_m_if():
    pass;

def create_options_m_if():
    pass;

def create_string_m_if():
    pass;


IDX_IF = 0;
IDX_PTR = 1;

class Gui2Argv:

    def __init__(self, stdscr, *ifds):
        self.ifds = ifds;
        self.ifs = [];
        self.destroyed = False;
        self.frame = tkinter.ttk.Frame(stdscr);

        #to enable fast scan of required inputs,
        # we use a linked-list style
        rptr = 0;

        for ptr, ifd in enumerate(self.ifds):
            typ = ifd.get(IFD_TYPE, IF_STRING);
            iF = None;

            # handle defaults

            default = ifd.get(IFD_DEFAULT, None);
            if isinstance(default, list):
                if default:
                    default = default.pop(0);
                # else, we can't trust that interfaces' factories can handle empty
                # default lists appriopriately
                else:
                    default = None;

            # there will always be checks on all inputs except options, though customizable.
            chk = self.check(ifd.get(IFD_CHECK, False));

            if typ == IF_STRING:
                iF = create_string_if(
                        self.frame,
                        ## name can be an empty string
                        ifd.get(IFD_NAME, ""),
                        default,
                        ifd.get(IFD_HINT, None),
                        chk,
                        default and ifd.get(IFD_REQUIRED, False),
                        );

            elif typ == IF_SPEC_FILE or typ == IF_FILE:
                iF = create_file_if(
                        self.frame,
                        ## name can be an empty string
                        ifd.get(IFD_NAME, ""),
                        default,
                        ifd.get(IFD_HINT, None),
                        chk,
                        default and ifd.get(IFD_REQUIRED, False),
                        );

            elif typ == IF_OPTIONS:
                iF = create_options_if(
                        self.frame,
                        ## name can be an empty string
                        ifd.get(IFD_NAME, ""),
                        ifd.get(IFD_CHOICES),
                        default,
                        ifd.get(IFD_HINT, None),
                        );

            if ifd.get(IFD_REQUIRED, False):
                # to prevent index error on the very first pass on the loop.
                if self.ifs:
                    self.ifs[rptr][IDX_PTR] = ptr;
                    rptr = ptr;

            tup = [0, 0];
            tup[IDX_PTR] = ptr;
            tup[IDX_IF] = iF;
            self.ifs.append(tup);

    # for access to the positional underlying Interface object

    def __getitem__ (self, idx):
        return self.ifs[idx];

    def show(self):
        if self.destroyed:
            raise KeyError("This instance has be destroyed and unusable");

        self.frame.place(x = 0, y = 0, relheight = 1, relwidth = 1);
        alen = len(self.ifs);
        for ia, ar in enumerate(self.ifs):
            ar[IDX_IF].name.place(relx = 0, rely = ia/alen, relwidth = 1/4);
            ar[IDX_IF].widget.place(relx = 1/4, rely = ia/alen, relwidth = 3/4);

        return True;

    
    def hide(self):
        if self.destroyed:
            raise KeyError("This instance has been destroyed and unusable");
        return self.frame.place_forget();

    def destroy(self):
        if self.destroyed:
            raise KeyError("This instance has been destroyed and unusable");
        
        self.destroyed = True;
        return self.frame.destroy();


    def append_interface(self, ifd):
        pass;

    def pop_interface(self, idx):
        pass;

    def get_argv_with_all_defaults(self, mx = MAX_DEFAULT_SIZE):
        return self.get_cmdline_with_all_defaults(mx).split();

    def get_cmdline_with_all_defaults(self, mx = MAX_DEFAULT_SIZE):
        cmdline = "";
        value = "";

        for idx, ifd in enumerate(self.ifds):
            # make the conditionals independent.

            # for defaults
            if isinstance(ifd[IFD_DEFAULT], list):
                for ix in range(mx):
                    try:
                        value = ifd[IFD_DEFAULT][ix];
                        if IFD_PSEUDOS in ifd and value in ifd[IFD_PSEUDOS] and not ifd[IFD_PSEUDOS].get(value):
                            continue;
                        
                        if IFD_PSEUDOS in ifd and value in ifd[IFD_PSEUDOS]:
                            value = ifd[IFD_PSEUDOS].get(value);

                        cmdline += "{prefix}{value}{suffix} ".format(
                                prefix = ifd.get(IFD_PREFIX, ""),
                                value = value,
                                suffix = ifd.get(IFD_SUFFIX, ""),
                                );

                    except IndexError:
                        break;

            
            if not self.ifs[idx][IDX_IF].ready:
                continue;

            if IFD_PSEUDOS in ifd and self.ifs[idx][IDX_IF].get_value() in ifd[IFD_PSEUDOS] and not ifd[IFD_PSEUDOS].get(self.ifs[idx][IDX_IF].get_value()):
                continue;



            if IFD_PSEUDOS in ifd and self.ifs[idx][IDX_IF].get_value() in ifd[IFD_PSEUDOS]:
                value = ifd[IFD_PSEUDOS].get(self.ifs[idx][IDX_IF].get_value());

            else:
                value = self.ifs[idx][IDX_IF].get_value();

            cmdline += "{prefix}{value}{suffix} ".format(
                    prefix = ifd.get(IFD_PREFIX, ""),
                    value = value,
                    suffix = ifd.get(IFD_SUFFIX, ""),
                    );

        return cmdline[:-1];


    def get_cmdline(self):
        cmdline = "";
        value = "";

        for idx, ifd in enumerate(self.ifds):
            if not self.ifs[idx][IDX_IF].ready:
                continue;

            elif IFD_PSEUDOS in ifd and self.ifs[idx][IDX_IF].get_value() in ifd[IFD_PSEUDOS] and not ifd[IFD_PSEUDOS].get(self.ifs[idx][IDX_IF].get_value()):
                continue;

            
            if IFD_PSEUDOS in ifd and self.ifs[idx][IDX_IF].get_value() in ifd[IFD_PSEUDOS]:
                value = ifd[IFD_PSEUDOS].get(self.ifs[idx][IDX_IF].get_value());

            else:
                value = self.ifs[idx][IDX_IF].get_value();

            cmdline += "{prefix}{value}{suffix} ".format(
                    prefix = ifd.get(IFD_PREFIX, ""),
                    value = value,
                    suffix = ifd.get(IFD_SUFFIX, ""),
                    );

        return cmdline[:-1];

    def get_argv(self):
        return self.get_cmdline().split();
    
    
    def _chk_ready(self):

        for i, if_ptr_tup in enumerate(self.ifs):
            ifd_cur = self.ifds[i];
            if not ifd_cur.get(IFD_REQUIRED, False):
                continue;


            ptr_cur = i;
            ptr_nxt = if_ptr_tup[IDX_PTR];

            while True:
                if not self.ifs[ptr_cur][IDX_IF].ready or not self.ifs[ptr_nxt][IDX_IF].ready:
                    return False;
                
                # end of list
                if ptr_cur == ptr_nxt:
                    break;

                ## because we move two steps(check two interfaces) in any one pass
                ptr_cur = self.ifs[ptr_nxt][IDX_PTR];
                ptr_nxt = self.ifs[ptr_cur][IDX_PTR];

            # because any unready input causes a return, otherwise a break
            return True;
            

    
    @property
    def ready(self):
        return self._chk_ready();

    def check(self, chk = False, *pargs, **kwargs):
        def _chk(iF, value):
            if callable(chk):
                iF.ready = chk(value);
            
            # remember, always check.
            else:
                iF.ready = bool(value);

            # null input should be visibilile to the user. 
            return True;


        return _chk;

import threading
import collections
import queue;

ACTIVITY_REPORT = 0;
ACTIVITY_LOGGER = 1;

MAX_LOG_SIZE = 50;

#this should be 8-bits.
#to post tasks with signums, these are bitwise Or'ed with a bitwise-right-shifted dashboard-identifying signum.
# this is to allow a variable-length commands for a dashboard for example.

SIG_CMD_EQUALS = 0;
SIG_CMD_CONTAINS = 1;

class Task:
    def __init__(self, tcall, *pargs, **kwargs):
        self.tcall = tcall;
        self.signum = None;
        self.sigargs = [];
        self.pargs = pargs;
        self.kwargs = kwargs;
        self.result = RNone();

    def __call__(self):
        if not self:
            self.result = self.tcall(*self.pargs, **self.kwargs);

        return self.result;

    def __bool__(self):
        return not isinstance(self.result, RNone);

    def wait(self):
        while not self:
            pass;

        return self.result;



class PQueue(queue.PriorityQueue):
    PRIORITY_WRITELOG = 0;
    PRIORITY_STATUS = 1;
    PRIORITY_NORMAL = 2; 
    def put(self, item, priority = None, *pargs, **kwargs):
        priority = self.PRIORITY_NORMAL if not priority else priority;
        return super().put((priority, item), *pargs, **kwargs);

class Activity:
    def __init__(self, size = 30):
        self.logs = collections.deque(size);
        self.size = size;
        self.lk = threading.Lock();

    def append_log(self, log):
        self.logs.append(log);

    def lock(self):
        return self.lk.acquire();

    def release(self):
        return self.lk.release();

    def __iter__(self):
        yield from iter(self.log);

class Dashboard:
    NO_ID = -1;
    ACTIVITY = "activity";
    REAL_ID = "real_id";

    def __init__(
            self,
            stdscr,
            scroll_granularity,
            pqueue,
            signum = None,
            sigbits = 8,
            activity_pauser = None,
            activity_player = None,
            mlogger = None,
            logsize = MAX_LOG_SIZE,
            ):
        self.stdscr = stdscr;
        self.scroll_granularity = scroll_granularity;
        self.dlist = [];
        self.ddata = {};
        self.counter = 0;
        self.signum = signum;
        self.sigbits = sigbits;
        self.pqueue = pqueue;
        self.mlogger = mlogger;
        self.logsize = logsize;
        self.activity_pauser = activity_pauser;
        self.activity_player = activity_player;
        self.id = self.NO_ID;
        self.c_lock = threading.Lock();
        self.a_lock = threading.Lock();
        self.is_live = False;
        self.items_var = tkinter.StringVar(value = self.dlist);
        self.frame = tkinter.ttk.Frame(stdscr);
        self.items_listbox = tkinter.Listbox(self.frame, listvariable = self.items_var);

        #hscrollbar = tkinter.Scrollbar(frame, orient = tkinter.HORIZONTAL, command =
        #        self.items_listbox.xview);

        self.vscrollbar = tkinter.Scrollbar(self.frame, orient = tkinter.VERTICAL, command =
                self.items_listbox.yview);

        #hscrollbar.place(x = 0, y = 0, relheight = 1/8, relwidth = 1);


        self.items_listbox.configure(yscrollcommand = self.vscrollbar.set);

        #items_listbox.configure(xscrollcommand = hscrollbar.set);

        #self.log = tkinter.scrolledtext.ScrolledText(self.frame, background = "black", foreground = "white", state='normal', wrap = "word");
        self.log = tkinter.Text(self.frame, background = "black", foreground = "white", state='normal', wrap = "word");
        self.logger = self.Logger(self, self.log);

    def __call__(self, task):
        #this a signum runner intended for the gui thread.
        # After identification with the object's signum, the thread should call the object.
        # it passes the task, with its signum modified for the object's command domain.
        if task.signum == SIG_CMD_CONTAINS and task.sigargs and task.sigargs[0] in self.ddata and self.ddata[task.sigargs[0]][REAL_ID]:
            task();

        elif self.id == self.NO_ID or (task.signum == SIG_CMD_EQUALS and task.sigargs and task.sigargs[0] == self.id):
            task();

        else:
            return False;

    def show(self):
        self.frame.place(x = 0, y = 0, relwidth = 1, relheight = 1);
        self.vscrollbar.place(x = 0, y = 0, relheight = 1, relwidth = 1/40);
        self.items_listbox.place(relx = 1/40, y = 0, relwidth = 1/3, relheight = 1);

        self.log.place(relx = 1/3 + 1/25, y = 0, relheight = 9/10, relwidth = 1 - (1/3 + 1/20));
        self.is_live = True;

    def get_activity(self, realid = None):
        realid = threading.get_ident() if not realid else realid;
        if not realid in self.ddata:
            return None;

        return self.ddata[realid][self.ACTIVITY];


    def alloc(self, aid = None):
        # a thread should call this at the start of its activity
        aid = threading.get_ident() if not aid else aid;
        if not aid in self.ddata:
            #add first.
            aid = self.add();

        elif self.ddata[aid][self.REAL_ID]:
            return self.ddata[aid];

        # remove the cookie.
        info = self.ddata.pop(aid);
        self.a_lock.acquire();
        info[self.REAL_ID] = len(self.dlist);
        self.dlist.append(str(aid));
        # for activity threads
        self.ddata[threading.get_ident()] = info;
        # for scrolls
        self.ddata[info[self.REAL_ID]] = info;
        self.a_lock.release();

        return info;

    def add(self, aid = None):
        # calling, without an 'aid', this before 'alloc' returns a cookie-ish id. This intended for
        # when an activity object is created and allocated later, 'alloc' replaces
        # the return cookie during allocation proper.

        if not aid:
            # for thread-safety, we lock the counter
            self.c_lock.acquire();
            aid = self.counter;
            self.counter += 1;
            self.c_lock.release();

        ac = Activity(size = self.logsize);

        self.ddata[aid] = {
                self.REAL_ID: None,
                self.ACTIVITY: ac,
                };

        return aid;
        
    def getcurrent(self):
        return self.id;

    def setcurrent(self, realid):
        # this should only be called in gui thread
        self.id = realid;
        self.logger.write_log(self.get_activity(realid));
        return True;

    
    # extends the parent class and does actual logging
    class Logger:
        def __init__(self, parent, log):
            self.log = log;
        
        def write_log(self, activity):
            self.log['state'] = 'normal';
            for msg in activity:

                if self.log.index('end-1c') != '1.0':
                    self.log.insert('end', '\n');

                self.log.insert('end', msg);

            self.log['state'] = 'disabled';

            #self.log.see("end-1c linestart");


        def append_log(self, msg):

            self.log['state'] = 'normal';

            if self.log.index('end-1c') != '1.0':
                self.log.insert('end', '\n');

            self.log.insert('end', msg);
            self.log['state'] = 'disabled';
            #self.log.see("end-1c linestart");

        
        def debug(self, msg, *pargs, **kwargs):
            return self.parent.mlogger.debug(msg, *pargs, **kwargs);

        def fatal(self, msg, *pargs, **kwargs):
            return self.parent.mlogger.fatal(msg, *pargs, **kwargs);

        def info(self, msg, *pargs, **kwargs):
            aid = threading.get_ident();

            self.parent.mlogger.info(msg, *pargs, **kwargs);

            act = self.parent.get_activity(aid);

            if not act:
                return False;

            cur = self.parent.getcurrent();

            if cur == self.parent.NO_ID:
                # special case, this should be done once for a programs lifetime
                tk = Task(self.parent.setcurrent, aid);
                if isinstance(self.parent.signum, int) and self.parent.signum >= 0:
                    tk.signum = (SIG_CMD_EQUALS << self.parent.sigbits) | self.parent.signum;
                    tk.sigargs = [aid];

                self.parent.pqueue.put(
                        tk,
                        self.PRIORITY_WRITELOG
                        );

            elif cur == aid:
                tk = Task(self.append_log, msg);
                if isinstance(self.parent.signum, int) and self.parent.signum >= 0:
                    tk.signum = (SIG_CMD_EQUALS << self.parent.sigbits) | self.parent.signum;
                    tk.sigargs = [aid];

                self.parent.pqueue.put(
                        tk,
                        self.PRIORITY_WRITELOG
                        );


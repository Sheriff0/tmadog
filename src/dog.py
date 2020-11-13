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

import status
import tasker
import libdogs

#CTYPE attributes
CTYPE_LEN = 2; #bits
CTYPE_MASK = 0xc0;

## 2-bits command type
## Currently, commands block (can't be run by send_task() independently) or
## otherwise (can be run on the calling thread by send_task()).

CTYPE_BLOCK = 0;
CTYPE_NOBLOCK = 1;

## CMD attributes
CMD_MASK = 0x3f;
CMD_SIZE = 6; #bits
CMD_MAX = 63; #max number of commands(from 0-62)

## type of the process counter (pc)
pc_type = int;

def MKCMD(cmd, ctype):
    return (ctype << CMD_SIZE) | cmd;

#A valid task id(magic) is 6 LSb command and 2 MSb type
CMD_NULL = MKCMD(0, CTYPE_NOBLOCK);
CMD_SUBMIT = MKCMD(1, CTYPE_BLOCK);
CMD_JOBS = MKCMD(2, CTYPE_NOBLOCK);
CMD_STATUS = MKCMD(3, CTYPE_NOBLOCK);


def GETCTYPE(cmd):
    return (cmd & CTYPE_MASK) >> CMD_SIZE;


def MKCTYPE(ctype, cmd):
    return ctype >> CMD_SIZE;


class DTask(tasker.Task):
    def __init__(self, *pargs, *kwargs):
        super ().__init__ (*pargs, **kwargs);

DTask.set_tdir(
        {
            CMD_SUBMIT: "submit",
            CMD_STATUS: "nop",
            CMD_JOBS: "nop",
            }
        );


class CmdlineErr(argparse.ArgumentError):
    def __init__(self, *pargs, *kwargs):
        super ().__init__ (*pargs, **kwargs);

parser = argparse.ArgumentParser ();
parser.add_argument ('--debug', action = 'store_true', help = 'To enable debug mode')
class Dog:
    def start(self):
        """start the dog loop - blocks until .end() is called somehow"""
        self.started = True;

        while self.started:
            if self.pc < self.tasktab_size:
                task = self.tasktab[self.pc];
                if task.state == tasker.TS_RUNNABLE:
                    self.run(task);

                    self.pc += 1;
    
    def run(self, task):
        return self.getcmd(task)(task);

    def getcmd(self, task):
        ## no need to check if a command is supported.
        ## DTask already did a good job when the task was initialized.
        if isinstance(task, self._InternalTask):
            return task.cmd;
        elif isinstance(task, DTask):
            return getattr(self, tasker.gettvalue(task));
        

    
    def end(self):
        """ends the dog - the thread (if any) that called start returns from it."""
        self.started = False;

    def get_tasks():
        pass;
    
    def jmp(self, task):
        ## emulate a processor jump using simple indirection rather than prepend the tasklist
        ## NOTE make thread-safe.

        # jmp format
        # ==========
        # task.status.message = "jmp"
        # 0 <= task.args < self.tasktab_size (return addr)
        # task.status.cause = task

        if not isinstance(task.status, status.Status) or isinstance(task.args,
                pc_type):
            return None;

        if self.getcmd(task) != self.jmp:
            # take action
            pass;

        if task.status.message == "jmp":
            ## do a return
            task.state = tasker.TS_EXITED;

            # to point pc rightly when .start() increments it
            self.pc = task.args - 1;
        else:
            lr = self._InternalTask(cmd = self.jmp, args = self.pc);

            st = status.Status(msg = "jmp", cause task);
            self.tasktab.extend([task, lr]);
            self.tasktab_size += 1;

            # self.tasktab_size -2 points to task but .start() increments pc
            # once the current task returns which will point to lr

            self.pc = self.tasktab_size - 3
    
    def update_index(self):
        pass;

    def send_task(
            self,
            task_or_str = DTask(), #send a null task
            ):
        task = None;

        if isinstance(task_or_str, str):
            tid = tasker.gettid(DTask(), task_or_str.split()[0]);
            if not tid:
                return None;
            task = DTask(
                    tid = tid,
                    args = task_or_str,
                    );
        elif isinstance(task_or_str, (DTask, self._InternalTask)):
            task = task_or_str;

        if task == None:
            return None

        elif GETCTYPE(task.tid) == CTYPE_NOBLOCK:
            return self.run(task);

        else:
            return self._alloc(task);
    
    def _alloc(self, task = None):
        if not isinstance(task, (DTask, self._InternalTask)):
            return None;

        self.tasktab.append(task);
        self.tasktab_size += 1;

    def stop_task(self, ta):
        if isinstance(ta, int):
            if ta < self.tasktab_size:
                self.tasktab[ta].state = tasker.TS_STOPED;
        elif isinstance(ta, (DTask, self._InternalTask)):
            ta.state = tasker.TS_STOPED;

        elif isinstance(ta, list):
            for t in ta:
                self.stop_task(t);

    def kill_task():
        pass;

    def __init__ (self, cmdline, amgr, initial_t = ""):
        self.arg_gens = scrm.QScrList();
        self.prep_argv = scrm.QScrList();
        self.prep_argc = 0;
        self.status = status.Status();
        self.pc = pc_type(0);
        self.tasktab = scrm.QScrList();
        self.tasktab_size = self.pc;
        self.amgr = amgr;

        #self.pq = [];
        #self.pqlen = 0;
        self.cmdline = scrm.QScrList();
        ## no more need for this as one navigator is shared
        ##self.navtab = scrm.QScrList ();
        
        ##instead do
        self.nav = None;

        self.setup_cmdline(cmdline);
        
        ## create navigator first if possible
        #self.setup_nav();

        ## can start run a task already (once start is called) before a frontend comes-up
        ## initial_t should be a cmdline string for the command
        self.send_task(initial_t);

        self.started = False;
    
    def release_nav(self, nav = None):
        if not nav:
            nav = self.nav;
        return libdogs.unassign(nav); 

    def get_nav(self, cli):
        if not self.prep_argv[0].one_nav:
            return libdogs.assign(cli);

        elif self.prep_argv[0].one_nav:
            if self.nav:
                self.nav = libdogs.assign(cli, self.nav);
        ## create navigator
            else:
                ## when no navigator is passed, libdogs.assign creates one and assign to the given cli.
                self.nav = libdogs.assign(cli);

            
        if not self.nav:
            status = status.Status(status.S_ERROR, "can't create navigator",
                    self.nav);

            self.status = status;
            return status;

        status = status.Status(status.S_OK, msg = "normal navigation target given");
        self.status = status;

        return self.nav;


    def setup_nav(self, tcaller = None):
        arg = None;

        while arg == None:
            arg = self.getarg_by_attr("url");
        ## create navigator
        
        try:
            self.nav = navigation.Navigator (
                    self.prep_argv[arg]["url"],
                    self.prep_argv[arg]["wmap"],
                    self.prep_argv[arg],
                    session = None, #NOTE create a new session
                    );

            status = status.Status(msg = "normal navigation target given");
        except BaseException as err:
            status = status.Status(status.S_ERROR, "can't create navigator",
                    err);


        if isinstance(tcaller, DTask):
            tcaller.status = status;

        self.status = status;

        return status;


    def setup_cmdline(self, cmdline, psr = None, preproc = None):
        
        try:
            if not psr:
                psr = parser;
                args = psr.parse_args(cmdline.split());
            elif psr and preproc:
                args = psr.parse_args(cmdline.split());
                arg_gen = preproc(args);

                self.arg_gens.append(arg_gen);
            else:
                args = psr.parse_args(cmdline.split());
            self.cmdline.append(
                    (
                        cmdline,
                        args,
                        )
                    );
            
            self.status = status.Status(status.S_OK, "cmdline parsed successfully")
            return args;

        except argparse.ArgumentError as err:
            status = status.Status("cmdline error", status.S_ERROR,
                    CmdlineErr(err,cmdline psr, preproc));
            return self.status;
        
        except BaseException as err:
            status = status.Status("Unknown Err", status.S_ERROR,
                    CmdlineErr(err,cmdline,psr,preproc)); 
            self.status = status;

            return self.status;


    def argv(self):
        """iterate over all arguments - raw and preprocessed.
        unlike the getarg_by_* functions that skip statuses, if a preprocessor returns a status
        instead of a valid argument that status is yielded too(but not appended
        to .prep_argv).
        """
        for arg in self.prep_argv:
            yield arg;

        for arg_gen in self.arg_gens:
            for arg in arg_gen:
                if not isinstance(arg, status.Status):
                    self.prep_argv.append(
                                arg,
                            );
                    self.prep_argc += 1;

                yield arg;

        

    def getarg_by_index(self, idx = 0):
        if not idx >= self.prep_argc:
            return idx;

        i = prep_argc - 1;

        for arg_gen in self.arg_gens:
            for arg in arg_gen:
                if not isinstance(arg, status.Status):
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
            for arg_gen in self.arg_gens:
                for arg in arg_gen:
                    if not isinstance(arg, status.Status):
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

    def idle(self):
        """ if the dog is idle """
        pass;

    def submit(self, task):
        if not hasattr(self, "submit_parser"):
            parser = argparse.ArgumentParser ("submit");
            parser.add_argument ('--matno', help = 'Your Matric Number', action
                    = libdogs.AppendList, dest = libdogs.P_USR);

            parser.add_argument ('--pwd', help = 'Your password',
                    action = libdogs.AppendList, dest = libdogs.P_PWD);

            parser.add_argument ('--crscode', help = 'Your target course',
                    action = libdogs.AppendList, dest = libdogs.P_CRSCODE);

            parser.add_argument ('--tma', 
                    help = 'Your target TMA for the chosen
                    course', action = libdogs.AppendList, dest = libdogs.P_TMA);

            setattr(self, "submit_parser", parser);

        if isinstance(task, (DTask, self._InternalTask)):
            ## answer from the tasklist
            if isinstance(task, DTask):
                ## do externals:
                ## parse
                ## ...
                ## ...
                args = self.setup_cmdline(task.args, psr = getattr(self,
                    "submit_parser"), preproc = libdogs.preprocess);
                if not args:
                    st = status.Status(status.S_ERROR);

                ## create the task leader, and
                ## use it to create members as needed,
                ## execute them and play them into the loop with a pre-executor.


                grp_leader = self._InternalTask(cmd = self.submit_pre_exec, args = args,
                       magic = GRP);
                
                ## to keep kick-start schedule pre-execution
                self.submit_pre_exec(grp_leader);

            elif isinstance(ta, self._InternalTask):
                ##handle those created elsewhere
                ## group leader
                LDR = 1;
                ## group member
                MBR = 0;
                ## do task created by me
                if not hasattr(ta, "magic"): 
                    return None;
                if ta.magic == LDR:
                    pass
                elif ta.magic == MBR:
                    pass;
                else:
                    ## NOTE don't know if this is appriopriate?
                    return None
        else:
            ## answer a direct external/internal call
            pass;

    def submit_pre_exec(self, task):
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
        ## group leader
        LDR = 1;
        ## group member
        MBR = 0;

        if not isinstance(task, DTask):
            self.status = status.Status(status.S_ERROR);
            return self.status;
        
        ldr = None;
        mbr = None;

        if task.magic == LDR:
            ldr = task;
            mbr = task.nxt;
        elif task.magic == MBR:
            ldr = task.group;
            mbr = task;
        
        if not mbr:
            self._alloc(ldr);
            # do create and do all members recursively
            if ldr.nxt:
                # members are already created - execute assuming they are in the
                # task list
                while ldr.next:
                    # execute
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
                # create them and pre_execute them
                prev = None;

                for arg in self.argv():
                    if not libdogs.is_arg_valid(ldr.args, arg):
                        continue;

                    mbr = self._InternalTask(magic = MBR, group = ldr, cmd =
                                self.nop, arg = arg);
                    if not ldr.nxt:
                        ldr.nxt = mbr;

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
                    self.status = st;
                    if prev:
                        prev.nxt = mbr;
                    prev = mbr;
                    self._alloc(mbr);

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
            return st;
    
    def submit_main(self, arg):

        nav = self.get_nav(arg);
        if not nav:
            return nav;###handle

        for ftype in libdogs.fetch_all(arg, nav):
            return libdogs.brute_submit(arg, nav, ftype);

    def nop(self):
        """like nop in x86 assembly"""
        pass;

    def clean(self):
        """ rid the tasklist of exited and zombied tasks possibly a locking mechanism
            to pause the .start() loop.
            can be called functions that dump the tasklist.
        """
        pass;
    
    class _InternalTask(DTask):
        """ instances of this can find themselves in tha tasktab.
            It is meant for use internally by method that want a task object that is ligther, laxer, and more
            customizable than tasker.DTask
            """
        def __init__(self, cmd, magic, *pargs, **kwargs):
            self.magic = magic
            self.cmd = cmd;
            super ().__init__ (*pargs, **kwargs);



def change(self, args):
    """change course code/tma number"""
    if "help" in args:
        return {
                "course_code": "course code e.g ABC232",
                "tma_no": "TMA number e.g 1, tma1",
                };

    crscode = self.getstr ("Course Code7: ")

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

def login_keyl108 (self, qscr = None):
    if not qscr or isinstance (qscr, bytearray):
        qscr = self.scr_mgr

    matno = self.getstr ("Matric No: ")
    pwd = self.getstr ("Password: ")
    crscode = self.getstr ("Course Code: ")
    tma = self.getstr ("Tma No(1-3): ")
    self.shutdown (qscr)

    if (not matno or re.fullmatch (matno, qscr [self.keys.UID], flags =
        re.I)) and (not crscode or re.fullmatch (crscode, qscr
            [self.keys.CRSCODE], flags = re.I)) and (not tma or re.fullmatch (tma, qscr
                [self.keys.TMA], flags = re.I)):
        qscr ["nav"]["tma_page"]
    else:
        if matno and re.fullmatch (r"\w+", matno):
            qscr [self.keys.UID] = matno

        if pwd and re.fullmatch (r"\w+", pwd):
            qscr [self.keys.PWD] = pwd

        if crscode and re.fullmatch (r"\w+", crscode):
            qscr [self.keys.CRSCODE] = crscode

        if tma and re.fullmatch (r"\w+", tma):
            qscr [self.keys.TMA] = tma

        self.boot (qscr)
        #qscr ["qst"] = None maybe unnecessary


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


def __getitem__ (self, attr):
    return getattr (self.scr_mgr ["qscr"], attr)

def printi (self, text = "", typ = PRINT_NONE):
    if not curses.isendwin ():
        self.cmdscr.move (self.LINES - 1, 0)
        self.cmdscr.clrtoeol ()
        self.cmdscr.touchline (0, self.LINES - 1, False)
        self.cmdscr.refresh ()
        curses.def_prog_mode()
        curses.reset_shell_mode ()
        print (typ.format (text))
        curses.reset_prog_mode ()

    else:
        print (typ.format (text))

    self.need_status = True

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

def enter10 (self, c = False):

    if self.scr_mgr ["qmode"] and self.scr_mgr ["qst"]:
        if c == False:
            c = self ["instr"] (len (self.scr_mgr ["qmgr"].pseudos [0]))

        c = c.decode ()

        self.scr_mgr ["qst"] [self.scr_mgr ["qmgr"].qmap ["ans"]] = c

        try:
            e = self.scr_mgr ["qmgr"].submit (self.scr_mgr ["qst"])

            x = re.search (r"(?P<mark>[01])\s*" + self.scr_mgr ["nav"].webmap ["fb"]["on_qst_submit"].strip (), self.scr_mgr ["qmgr"].sres.text, re.I)

            if x:
                self.amgr.check (self.scr_mgr ["qst"], int (x.group ("mark")), e)
            return self.message (self.scr_mgr ["qmgr"].sres)

        except:

            self.scr_mgr ["qst"] = None
            return self.update_qscr ()

    else:

        post_fetch_h = self.update_qscr
        post_fetch_arg = ()

        try:
            qst = self.scr_mgr ["qmgr"].fetch (timeout = (30.5, 60))

            if qst and isinstance (qst, lxml.html.FieldsDict):

                x = copy.deepcopy (qst)

                x = self.amgr.answer (x)

                if x and x != ansm.ANS_NOANSWER and qst [self.scr_mgr ["qmgr"].qmap ["qid"]] == x [self.scr_mgr ["qmgr"].qmap ["qid"]]:
                    qst = x

                self.pq.append ((qst [self.scr_mgr ["qmgr"].qmap ["crscode"]], qst
                    [self.scr_mgr ["qmgr"].qmap ["qid"]]))

                self.pqlen += 1

                self.scr_mgr ["lpqidx"] = self.pqlen - 1
                self.scr_mgr ["pqidx"] = self.scr_mgr ["lpqidx"]

                self.scr_mgr ["qmode"] = True

                post_fetch_arg = (qst,)
                curses.flushinp() #For safety

            else:
                post_fetch_h = self.message
                post_fetch_arg = (self.scr_mgr ["qmgr"].qres,)

        except:
            post_fetch_arg = (None,)
            self.scr_mgr ["qst"] = None
        return post_fetch_h (*post_fetch_arg)

def message (self, res):

    y = lxml.html.fromstring (res.text).text_content ()

    self.scr_mgr ["qscr"].clear ()

    self.scr_mgr ["qscr"].addstr (0, 0, y)

    self.msgyx = [0]

    self.msgyx.append ((self.scr_mgr ["qscr"].getyx ()[0] + 1) * self.scr_mgr.scrdim
            [1])

    self.scr_mgr ["qline"] = 0

    self.doupdate ()

    self.scr_mgr ["qmode"] = False

def update_qscr (
        self,
        qst = None,
        flags = PRT_PRINT_QST | PRT_PRINT_CHOICES,
        qpaint = curses.A_NORMAL,
        opaint = curses.A_NORMAL,
        apaint = curses.A_BLINK
        ):

    if qst:
        self.scr_mgr ["qst"] = qst

    elif not self.scr_mgr ["qst"]:
        self.scr_mgr ["qline"] = 0
        self.scr_mgr ["qscr"].clear ()
        self.scr_mgr ["qscr"].addstr (0, 0, "Hit Enter to start")

        self.doupdate ()

        return



    if not (PRT_KEEPLINE & flags):
        self.scr_mgr ["qline"] = 0
        fcur = None

    else:
        fcur = self.scr_mgr ["qscr"].getyx ()

    if (PRT_PRINT_CHOICES & flags) and (PRT_PRINT_QST & flags):
        self.scr_mgr ["qscr"].clear ()


    if PRT_PRINT_QST & flags:
        if isinstance (self.scr_mgr ["qst"] [self.scr_mgr ["qmgr"].qmap ["qn"]], int):
            self.scr_mgr ["qscr"].addch (self.scr_mgr ["qmgr"].pseudos [i])
            pre = ""
        else:
            pre = str (self.scr_mgr ["qst"] [self.scr_mgr ["qmgr"].qmap ["qn"]]) + ". "

        self.scr_mgr ["qscr"].addstr (0, 0, pre + self.scr_mgr ["qst"] [self.scr_mgr ["qmgr"].qmap ["qdescr"]].strip () + "\n\n", qpaint)


    obitmap = 1 if PRT_PRINT_CHOICES & flags else (flags & 0x7f) >> 3

    if obitmap:
        ol = len (self.scr_mgr ["optmap"])

        for opt in ["opt" + chr (97 + i) for i in range (len (self.scr_mgr ["qmgr"].pseudos))]:
            if obitmap & 1:
                i = (ord (opt[-1]) & 0x1f) - 1
                df = ol - i

                if df <= 0:
                    self.scr_mgr ["optmap"].extend (range (abs (df) + 1))
                    ol += abs (df + 1)

                if PRT_PRINT_QST & flags:
                    w = self.scr_mgr ["qscr"].getyx ()
                else:
                    if df > 0:
                        w = self.scr_mgr ["optmap"][i]
                    else:
                        w = self.scr_mgr ["qscr"].getyx ()

                y, x = w[0], 0

                if isinstance (self.scr_mgr ["qmgr"].pseudos [i], int):
                    self.scr_mgr ["qscr"].addch (self.scr_mgr ["qmgr"].pseudos [i])
                    pre = ""
                else:
                    pre = self.scr_mgr ["qmgr"].pseudos [i] + ": "


                self.scr_mgr ["qscr"].addstr (y, x, pre + self.scr_mgr ["qst"] [self.scr_mgr ["qmgr"].qmap [opt]].strip ())

                if PRT_PRINT_QST & flags:
                    cur = self.scr_mgr ["qscr"].getyx ()
                    l = (cur [0] - w[0]) * (self.scr_mgr.scrdim [1]) + cur [1]

                else:
                    l = self.scr_mgr ["optmap"][i][1]

                self.scr_mgr ["optmap"][i] = [
                    w[0],
                    l,
                    self.scr_mgr ["qmgr"].pseudos [i] if isinstance (self.scr_mgr ["qmgr"].pseudos [i], int) else None,
                    opaint
                    ]

                self.scr_mgr ["qscr"].addch ("\n")

            if not PRT_PRINT_CHOICES & flags:
                obitmap >>= 1



        if not self.scr_mgr ["optmap"]:
            pass #NOTE: Draw a textbox for fill-in-the-gap answer


        elif self.scr_mgr ["qst"] [self.scr_mgr ["qmgr"].qmap ["qid"]] != "error":

            a = self.scr_mgr ["qst"] [self.scr_mgr ["qmgr"].qmap ["ans"]]

            if a:
                i = self.scr_mgr ["qmgr"].pseudos.index (a)

                self.scr_mgr ["optmap"] [i][-1] = apaint

            else:
                i = 0

        else:
                i = 0

        self.paint (self.scr_mgr ["optmap"] [i])

    if PRT_KEEPCUR & flags:
        self.scr_mgr ["qscr"].move (*fcur)


    self.doupdate ()

    return

def ctrl_l12 (self, *args):
    #curses.flash ()
    self.stdscr.clear ()
    self.overwrite (self.scr_mgr ["qscr"], self.stdscr, self.scr_mgr ["qline"], 0, self.scr_mgr.scord[0], self.scr_mgr.scord [1],
    (self.scr_mgr.scrdim [0] + self.scr_mgr.scord [0]) - 1 - self.saloc, (self.scr_mgr.scrdim [1] + self.scr_mgr.scord
        [1]) - 1)

    self.status (1)
    self.stdscr.clearok (True)
    self.stdscr.noutrefresh ()
    curses.doupdate ()

def ctrl_c3 (self, *args):
    return BREAK

def key_resize410 (self, *pargs):
    return self.resize

def resize (self, stdscr):
    self.stdscr = stdscr
    self.LINES, self.COLS = self.stdscr.getmaxyx ()
    self.cmdscr = curses.newwin (self.LINES, self.COLS)

    r = self.scr_mgr.resize (self.stdscr)
    if r and r != -1:
        for scr, inc in r:
            self.update_qscr (
                    scr ["qst"] if not inc else None,
                    flags = PRT_PRINT_CHOICES | PRT_PRINT_QST | PRT_KEEPLINE if inc else PRT_PRINT_QST | PRT_PRINT_CHOICES)
        self.status (1)
        self.doupdate ()
        return inc

    else:
        return r

def ctrl_w23 (self, offset = b"1"):
    if not offset.isdigit ():
        return

    offset = int (offset.decode ())
    self ["keypad"] (True)
    c = self ["getch"] ()

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
    self.saloc = 2 if self.scr_mgr.scrdim [0] > 2 else 0

    if self.saloc:
        self.stdscr.move (self.scr_mgr.scord [0] + self.scr_mgr.scrdim [0] -
                self.saloc, 0)
        self.stdscr.clrtoeol ()
        self.stdscr.addnstr (self.scr_mgr.scord [0] + self.scr_mgr.scrdim [0] - self.saloc, 0,
                "%s %s TMA%s" % (self.scr_mgr [self.keys.UID].upper (),
                    self.scr_mgr [self.keys.UID1].upper (), self.scr_mgr
                    [self.keys.UID2]), self.scr_mgr.scrdim [1])
        self.stdscr.chgat (self.scr_mgr.scord [0] + self.scr_mgr.scrdim [0]
                - self.saloc, 0 ,
                curses.A_REVERSE | (curses.A_BOLD if highlight else 0))

def paint (self, t = None, color = curses.A_BOLD | curses.A_REVERSE,
        undo = False, optmap = None):

    if t == None:
        optmap = optmap if optmap else self.scr_mgr ["optmap"]

        if not optmap:
            return

        cur = self.scr_mgr ["qscr"].getyx ()

        t = [x for x in optmap if x [0] == cur [0]]

        if not t:
            return

        else:
            t = t[0]

    c = divmod (t [1], self.scr_mgr.scrdim [1])
    l = t [0]

    x = c[0]

    while x:
        self.scr_mgr ["qscr"].chgat (l, 0, (color) if not undo
                else t[-1])
        l += 1
        x -= 1

    self.scr_mgr ["qscr"].chgat (l, 0, c [1], (color) if not undo
            else t [-1])

    if t [2]:
        self.scr_mgr ["qscr"].addch (t[0], 0, t[2])

    self.scr_mgr ["qscr"].move (t[0], 0)

def ctrl_r18 (self):
    if self.scr_mgr ["qmode"] and self.scr_mgr ["qst"]:
        qst = self.scr_mgr["qst"].copy ()

        for k, v in self.scr_mgr ["nav"].webmap ["retros"].items ():
            if k not in qst:
                break
            qst [k] = v

        return self.update_qscr (qst)

def increaseQn_keyPlus43 (self, addend = None):
    if self.scr_mgr ["qmode"] and self.scr_mgr ["qst"]:
        if addend:
            try:
                addend = int (addend.decode())
            except ValueError:
                return
        else:
            addend = 1

        qst = self.scr_mgr ["qst"].copy ()
        n = math.trunc (int (qst [self.scr_mgr ["qmgr"].qmap ["qn"]] + "0") / 10) + addend

        qst [self.scr_mgr ["qmgr"].qmap ["qn"]] = str (n)

        self.update_qscr (qst, flags = PRT_PRINT_CHOICES | PRT_PRINT_QST | PRT_KEEPLINE)

def increaseTotscrore_keyAsterik42 (self, addend = None):
    if self.scr_mgr ["qmode"] and self.scr_mgr ["qst"]:
        if not addend or not addend.isdigit ():
            addend = 1
        else:
            addend = int (addend.decode())

        qst = self.scr_mgr ["qst"].copy ()
        n = math.trunc (int (qst [self.scr_mgr ["qmgr"].qmap ["score"]] + "0") / 10) + addend

        qst [self.scr_mgr ["qmgr"].qmap ["score"]] = str (n)

        self.update_qscr (qst, flags = PRT_PRINT_CHOICES | PRT_PRINT_QST | PRT_KEEPLINE)


def chCrscode_keyCaret94 (self, crscode = bytearray ()):
    if self.scr_mgr ["qmode"] and self.scr_mgr ["qst"]:
        crscode = crscode.decode()

        qst = {}

        for k,v in self.scr_mgr ["qst"].copy ().items ():
            if isinstance (v, str):
                v = re.sub (r"(?P<cs>" + self.scr_mgr ["crscode"] + ")",
                        self.scr_mgr ["qmgr"]._copycase (crscode), v, flags =
                        re.I)
            qst [k] = v

        self.update_qscr (qst, flags = PRT_PRINT_CHOICES | PRT_PRINT_QST | PRT_KEEPLINE)

def discoverAns_keyQuotemark33 (self, mod = bytearray ()):
    if self.scr_mgr ["qmode"] and self.scr_mgr ["qst"]:


        matno = "Nou123456789"

        try:
            mod = 0 if not mod else int (mod.decode ()) - 1

        except ValueError:
            return

        def mask (dic, pat, sub):
            dic1 = requests.structures.OrderedDict ()
            for k, v in dic.items ():
                if isinstance (v, str):
                    v = re.sub (r"(?P<cs>" + pat + ")",
                            self.scr_mgr ["qmgr"]._copycase (sub), v, flags =
                            re.I)
                dic1 [k] = v

            return dic1


        count = 0

        qst = self.scr_mgr ["qst"]
        c = self ["instr"] (len (self.scr_mgr ["qmgr"].pseudos [0]))

        c = c.decode ()

        qst [self.scr_mgr ["qmgr"].qmap ["ans"]] = c

        while mod: #Answer Discovery loop
            self.echo ("Trying to discover answer to question %s, Please wait..." % (qst
                [self.scr_mgr ["qmgr"].qmap ["qn"]],))

            qst1 = mask (qst, self.scr_mgr [self.keys.UID], matno)

            for a in dogs.AnyheadList (self.scr_mgr ["qmgr"].pseudos, qst1 [self.scr_mgr ["qmgr"].qmap ["ans"]]):

                qst1 [self.scr_mgr ["qmgr"].qmap ["ans"]] = a

                try:
                    e = self.scr_mgr ["qmgr"].submit (qst1)

                    x = re.search (r"(?P<mark>[01])\s*" + self.scr_mgr ["nav"].webmap ["fb"]["on_qst_submit"].strip (), self.scr_mgr ["qmgr"].sres.text, re.I)

                    if x:
                        x = int (x.group ("mark"))
                        self.amgr.check (qst1, x, e)
                        if x == 1:
                            qst [self.scr_mgr ["qmgr"].qmap ["ans"]] = a

                            self.echo ("Done. Unmasking %s for submission" % (self.scr_mgr [self.keys.UID],))
                            e = self.scr_mgr ["qmgr"].submit (qst)

                            x = re.search (r"(?P<mark>[01])\s*" + self.scr_mgr ["nav"].webmap ["fb"]["on_qst_submit"].strip (), self.scr_mgr ["qmgr"].sres.text, re.I)

                            if not x or int (x.group ("mark")) == 0:
                                raise TypeError ()
                            self.echo ("Done.")
                            break

                    else:
                        self.echo ("Error.")
                        raise TypeError ()
                except:
                    return self.message (self.scr_mgr ["qmgr"].sres) if hasattr (self.scr_mgr ["qmgr"], "sres") else None

            qst = self.scr_mgr ["qmgr"].fetch (timeout = (30.5, 60))

            if not qst or not isinstance (qst, lxml.html.FieldsDict):
                return self.message (self.scr_mgr ["qmgr"].qres) if hasattr (self.scr_mgr ["qmgr"], "qres") else None

            x = copy.deepcopy (qst)

            x = self.amgr.answer (x)

            if x and x != ansm.ANS_NOANSWER and qst [self.scr_mgr ["qmgr"].qmap ["qid"]] == x [self.scr_mgr ["qmgr"].qmap ["qid"]]:
                qst = x

            self.pq.append ((qst [self.scr_mgr ["qmgr"].qmap ["crscode"]], qst
                [self.scr_mgr ["qmgr"].qmap ["qid"]]))

            self.pqlen += 1

            self.scr_mgr ["lpqidx"] = self.pqlen - 1
            self.scr_mgr ["pqidx"] = self.scr_mgr ["lpqidx"]

            self.echo ("Done.")
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



parser.add_argument ('--debug', action = 'store_true', help = 'To enable debug mode')
parser.add_argument ('--qstdump', default = 'dumpqst.json', help = 'The dump file for questions')
parser.add_argument ('--database', '-db', default = 'olddb', help = 'The database to use')
parser.add_argument ('--noupdatedb', '-nodb', action = 'store_false', dest =
        'updatedb', default = True, help = 'Update the database in use')
parser.add_argument ('--url', help = 'The remote url if no local server',
        action = 'append', required = True)
parser.add_argument ('--matno', help = 'Your Matric Number', action = 'append')

parser.add_argument ('--pwd', help = 'Your password',
        action = 'append')

parser.add_argument ('--crscode', help = 'Your target course', action = 'append')

parser.add_argument ('--tma', help = 'Your target TMA for the chosen course', action = 'append')


parser.add_argument ('--cookies', help = 'Website cookies', action = 'append')

parser.add_argument ('--output', help = "output file format");

parser.add_argument ('--config', default = 'dogrc', help = 'configuration file to use', dest = 'wmap')

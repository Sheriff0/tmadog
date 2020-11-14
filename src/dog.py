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
            st = libdogs.brute_submit(arg, nav, ftype);
            if st.code == status.S_FATAL:
                break;

        return st;


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

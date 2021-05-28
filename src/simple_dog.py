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

import status
import tasker
import libdogs
import pathlib

STAT_ARG = 0;
STAT_ST = 1;

## group leader
SUB_LDR = 1;
## group member
SUB_MBR = 0;


def dog_submit_stat(dog):
    for ta in dog.tasktab:
        if not hasattr(ta, "magic") or ta.magic != SUB_MBR:
            continue;

        yield [ta.args, ta.status];

class SimpleDog:

    def __init__ (self, usrs, amgr, get_nav, outfile = None, **req_args):
        self.arg_gens = [];
        self.prep_argv = [];
        self.prep_argc = 0;
        self.status = status.Status();
        self.tasktab = [];
        self.tasktab_size = 0;
        self.amgr = amgr;
        self.usrs = usrs;
        self.nav = None;
        self.get_nav = get_nav;
        self.outfile = outfile;
        self.req_args = req_args;


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

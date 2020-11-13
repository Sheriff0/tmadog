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

## group leader
SUB_LDR = 1;
## group member
SUB_MBR = 0;

class SimpleDog:

    def __init__ (self, usrs, amgr):
        self.arg_gens = scrm.QScrList();
        self.prep_argv = scrm.QScrList();
        self.prep_argc = 0;
        self.status = status.Status();
        self.tasktab = scrm.QScrList();
        self.amgr = amgr;
        self.usrs = iter(usrs);
        self.nav = None;

    def get_nav(self, cli):
        self.nav = libdogs.assign(cli, self.nav);
        return self.nav;


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
        if not hasattr(task, "magic"):
            task = self._InternalTask(cmd = self.submit_pre_exec, args = task.args,
                   magic = SUB_LDR);
        
        ## to keep kick-start schedule pre-execution
        return self.submit_pre_exec(task);

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
            self._alloc(ldr);
            # do create and do all members recursively
            if ldr.nxt:
                # members are already created - execute assuming they are in the
                # task list
                while ldr.nxt:
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
                prev = ldr;

                for arg in self.argv():
                    mbr = self._InternalTask(magic = SUB_MBR, group = ldr, cmd =
                                self.nop, args = arg);
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

        return self.status;
    
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

    class _InternalTask(DTask):
        """ instances of this can find themselves in tha tasktab.
            It is meant for use internally by method that want a task object that is ligther, laxer, and more
            customizable than tasker.DTask
            """
        def __init__(self, cmd, magic, *pargs, **kwargs):
            self.magic = magic
            self.cmd = cmd;
            super ().__init__ (*pargs, **kwargs);

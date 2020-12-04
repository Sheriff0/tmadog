import status
import copy
import libdogs

## task states
## the runner is on it
TS_RUNNING = 0b0001;

## finished its job can't be runnable
TS_EXITED = 0b0010;

## stopped can be runable again
TS_STOPED = 0b0100;

## the task can be run
TS_RUNNABLE = 0b1000;

## can be used to keep a status alive even after a runner's (eg Dog) main status
## is changed
TS_ZOMBIE = 0b10000;

## stopped and can't run again
TS_TERM = 0b100000;

## task diposition (whether it can be listed on not) e.g - when a navigator
## can't  be set the setter function can create a hidden task that will
## eventually set the navigator when the neccasary argument are given (usually
## by blocking the dog runtime while waiting). This task shouldn't, normally, be shown to
## users.

TDISP_PUBLIC = 0;
TDISP_HIDDEN = 1;

class NoTask(BaseException):
    def __init__(self, *pargs, **kwargs):
        super ().__init__ (*pargs, **kwargs);

##task utility
def gettid(task, st):
    cidx = None;
    for pair in task.tid_tab.items():
        if not cidx:
            for i,a in enumerate(pair):
                if isinstance(st, type(a)):
                    cidx = i;
                    break;

            if cidx == None:
                return None;

        if st == pair[cidx]:
            return t;

def gettvalue(task):
    return task.tid_tab[task.tid];

class Task:
    tid_tab = {};

    @staticmethod
    def set_tdir(Task, tdir):
        if not tdir or (hasattr(tdir, "__setitem__") and hasattr(tdir, "__getitem__") and hasattr(tdir, "__contains__")):
            raise TypeError("Invalid Task directory");

        Task.tid_tab = libdogs.copy(tdir);

    def __init__ (self, tid = 0, args = None, status = None, group = None, nxt =
            None, state = TS_RUNNABLE,
            disp = TDISP_PUBLIC):

        tid = gettid(self, tid);

        if not tid or tid not in self.tid_tab:
            raise NoTask("Invalid Task", tid);

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
        self.tgroup = group;

    def __str__(self):
        return str(self.tid_tab[self.tid]);


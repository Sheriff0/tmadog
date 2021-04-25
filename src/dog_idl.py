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

    ## Depending on the type of interface, some checks can be performed on the
    ## user input; e.g checking if a file is non-empty. To customize the check,
    ## assign to a callable that returns True when input checks and False
    ## otherwise.

    "check": True,

    "hint": "Type all your names (5 max)",

    "default": None,
}
"""

import tkinter, tkinter.Label

IF_FILE = 0;
IF_SPEC_FILE = 1;
IF_OPTIONS = 2;
IF_STRING = 3;

IF_FILE_M = 0 | ord('m');
IF_SPEC_FILE_M = 1 | ord('m');
IF_OPTIONS_M = 2 | ord('m');
IF_STRING_M = 3 | ord('m');

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

        if v:
            iF.set_value(v);
            iF.ready = True;

        if cb and callable(cb):
            return cb(iF, v);

    return _gf;


## Factory functions for the various interface types

def create_file_if(stdscr, name, options, default = None, hint = None,
        def_on_empty = False):
    
    iF = create_string_if(
            stdscr,
            name,
            default = default,
            hint = hint,
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
    
    name_w = IfName(name, stdscr); #justify = tkinter.LEFT;
    
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

    name_w = IfName(name, stdscr); #justify = tkinter.LEFT;

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



class Gui2Argv:
    IDX_IF = 0;
    IDX_PTR = 1;

    def __init__(self, stdscr, *ifds):
        self.ifds = ifds;
        self.ifs = [];
        self._ready = False;
        self.destroyed = False;
        self.no_required = True;
        self.frame = tkinter.ttk.Frame(stdscr);

        #to enable fast scan of required inputs,
        # we use a linked-list style
        rptr = 0;

        for ptr, ifd in enumerate(self.ifds):
            typ = ifd.get("type", IF_STRING);
            iF = None;
            if typ == IF_STRING:
                chk = self.check(ifd.get("check", False));
                iF = create_string_if(
                        stdscr,
                        ## name can be an empty string
                        ifd.get("name", ""),
                        ifd.get("default", None),
                        ifd.get("hint", None),
                        chk,
                        ifd.get("default", None) and ifd.get("required", False),
                        );

            elif typ == IF_SPEC_FILE or typ == IF_FILE:
                iF = create_file_if(
                        stdscr,
                        ## name can be an empty string
                        ifd.get("name", ""),
                        ifd.get("default", None),
                        ifd.get("hint", None),
                        ifd.get("default", None) and ifd.get("required", False),
                        );

            elif typ == IF_OPTIONS:
                iF = create_options_if(
                        stdscr,
                        ## name can be an empty string
                        ifd.get("name", ""),
                        ifd.get("choices"),
                        ifd.get("default", None),
                        ifd.get("hint", None),
                        );

            if ifd.get("required", False):
                ifs[rptr][IDX_PTR] = ptr;
                rptr = ptr;

            if ifd.get("required", False):
                self.no_required = False;

            tup = [0, 0];
            tup[IDX_PTR] = ptr;
            tup[IDX_IF] = iF;
            self.ifs.append(tup);

    def show(self):
        if not self.destroyed:
            raise KeyError("This instance has be destroyed and unusable");

        self.frame.place(x = 0, y = 0, relheight = 1, relwidth = 1);
        for ia, ar in enumerate(self.ifs):
            ar.name.place(relx = 0, rely = ia/alen, relwidth = 1/4);
            ar.widget.place(relx = 1/4, rely = ia/alen, relwidth = 3/4);

        return True;

    
    def hide(self):
        if not self.destroyed:
            raise KeyError("This instance has been destroyed and unusable");
        return self.frame.place_forget();

    def destroy(self):
        if not self.destroyed:
            raise KeyError("This instance has been destroyed and unusable");
        
        self.destroyed = True;
        return self.frame.destroy();


    def append_interface(self, ifd):
        pass;

    def pop_interface(self, idx):
        pass;

    def get_cmdline(self):
        cmdline = "";

        for idx, ifd in enumerate(self.ifds):
            if not self.ifs[idx][IDX_IF].ready:
                continue;

            cmdline += "{prefix}{name}{value}{suffix} ".format(
                    prefix = ifd.get("prefix", ""),
                    name = ifd.get("name", ""),
                    value = self.ifs[idx][IDX_IF].get_value(),
                    ifd.get("suffix", ""),
                    );

        return cmdline[:-1];

    def get_argv(self):
        return self.get_cmdline().split();
    
    
    def _chk_ready(self):
        for i, if_ptr_tup in enumerate(self.ifs):
            ifd_cur = self.ifds[i];
            if not ifd_cur.get("required", False):
                continue;


            ptr_cur = i;
            ptr_nxt = if_ptr_tup[IDX_PTR];

            while True:
                if not self.ifs[ptr_cur][IDX_IF].ready or not self.ifs[ptr_nxt][IDX_IF].ready:
                    self._ready = False;
                    return self._ready;
                
                if ptr_cur == ptr_nxt:
                    return self._ready;

                ## because we move two steps(check two interfaces) in any one pass
                ptr_cur = self.ifs[ptr_nxt][IDX_PTR];
                ptr_nxt = self.ifs[ptr_cur][IDX_PTR];
            
            #finally, after all interface(s) checked
            self._ready = True;

        return self._ready;
    
    @property
    def ready(self):
        return self._chk_ready();

    def check(self, chk = False, *pargs, **kwargs):
        def _chk(iF, value):
            if callable(chk):
                iF.ready = chk(value);

            elif chk:
                iF.ready = bool(value);


            if not iF.ready:
                self._ready = False;
                return False;
            
            elif self.no_required:
                self._ready = True;
                return iF.ready;
            
            self._chk_ready();
            
            return iF.ready;


        return _chk;


import json, re
import time
import math
import sys
import argparse
import libdogs
import requests
import pathlib

upload_url = "https://content.dropboxapi.com/2/files/upload";

download_url = "https://content.dropboxapi.com/2/files/download";

delete_url = "https://api.dropboxapi.com/2/files/delete";

list_url = "https://api.dropboxapi.com/2/files/list_folder";

key = "zxK60VpMtmwAAAAAAAAAAZ76lD62i4GvL5SxC9ZgkQpIrpV4cReqSh0-SoujeAtZ";

MAX_WAIT_SEC = 10;


def gen_whitelisted_key(nlist):
    hdrs = Base_headers();
    key = time.time();
    hdrs["Dropbox-API-Arg"] = json.dumps(
            {
                "path": "/%s" % (key,),
                "mode": "overwrite",
                "mute": True,
                }
            );
    
    hdrs["Content-Type"] = "application/octet-stream";
    
    data = {
            "ts": 0,
            "whitelist": [],
            "nlist": nlist,
            };

    res = libdogs.goto_page3("POST", upload_url, headers = hdrs, data =
            json.dumps(data));
    
    if not res:
        return res;

    return KeyInfo(key, data);


def gen_key_with_epoch(x):
    return KeyInfo("".join(str(time.time()).split(".")));


def fetch_keyinfo(key, requester = libdogs.goto_page3):
    if not key:
        return None;


    res = fetch_file(key, requester);
    
    if not res:
        return res;

    return KeyInfo(key, json.loads(res));



def rm_key(keyobj):
    hdrs = Base_headers();
    hdrs["Content-Type"] = "application/json";

    return libdogs.goto_page3(
            "POST",
            delete_url,
            headers = hdrs,
            data = json.dumps(
                {
                    "path": "/%s" % (keyobj,),
                    }
     
                )
            );



def put_key(keyobj):
    hdrs = Base_headers();

    keyobj["mtime"] = int(keyobj.get("mtime", -1)) + 1;
    hdrs["Dropbox-API-Arg"] = json.dumps(
            {
                "path": "/%s" % (keyobj,),
                "mode": "overwrite",
                "mute": True,
                }
            );
    hdrs["Content-Type"] = "application/octet-stream";

    return libdogs.goto_page3("POST", upload_url, headers = hdrs, data = json.dumps(keyobj));

    
def update_key(key, updater = libdogs.goto_page3):
    hdrs = Base_headers();
    hdrs["Dropbox-API-Arg"] = json.dumps(
            {
                "path": "/%s" % (key,),
                }
            );

    res = updater("GET", download_url, headers = hdrs);
    
    if not res:
        return res;

    keyobj = json.loads(res.text);
    
    keyobj.update(key);

    keyobj["mtime"] = int(keyobj.get("mtime", -1)) + 1;
    hdrs["Dropbox-API-Arg"] = json.dumps(
            {
                "path": "/%s" % (key,),
                "mode": "overwrite",
                "mute": True,
                }
            );
    hdrs["Content-Type"] = "application/octet-stream";

    return updater("POST", upload_url, headers = hdrs, data = json.dumps(keyobj));


def alloc_key(key, requester = libdogs.goto_page3):
    hdrs = Base_headers();
    res = fetch_file(key, requester);
    
    if not res:
        return res;

    keyobj = json.loads(res);
    
    if "ts" in keyobj and int(keyobj["ts"]):
        return False;

    if isinstance(key, dict):
        keyobj.update(key);

    keyobj["ts"] = int(keyobj.get("ts", 0)) + 1;
    keyobj["mtime"] = int(keyobj.get("mtime", -1)) + 1;
    
    res = write_file(key, json.dumps(keyobj), requester);
    if not res:
        return res;

    return KeyInfo(key, keyobj);

def dealloc_key(key, requester = libdogs.goto_page3):
    hdrs = Base_headers();
    res = fetch_file(key, requester);
    
    if not res:
        return res;

    keyobj = json.loads(res);
    
    keyobj["ts"] = 0;
    keyobj["mtime"] = 0;
    
    res = write_file(key, keyobj, requester);
    if not res:
        return res;

    return KeyInfo(key, keyobj);



class Whitelist(list):
    def append(self, st):
        if str(st) in self:
            return False;

        super().append(str(st));

    def __contains__(self, val):
        for v in self:
            if re.fullmatch(v, str(val), re.I):
                return True;

        return False;


class KeyMgr:
    def __init__(self, keyinfo, kpath, updater = libdogs.goto_page3):
        self.kpath = kpath;
        self.keyinfo = keyinfo;
        self.updater = updater;
        rkinfo = dropbox.fetch_keyinfo(str(self.keyinfo), self.updater);
        if not rkinfo:
            raise LookupError("Could not fetch remote key file", rkinfo);

        if rkinfo.get("mtime", 0) > self.keyinfo.get("mtime", 0):
            self.keyinfo.update(rkinfo);
        
        # do some lowkey allocation if prev attempts failed
        self.keyinfo["ts"] = int(self.keyinfo.get("ts", 0)) + 1 if not int(self.keyinfo.get("ts", 0)) else self.keyinfo["ts"];

        self.keyinfo["user_whitelist"] = set(self.keyinfo.get("user_whitelist", []));
        self.keyinfo["crs_whitelist"] = set(self.keyinfo.get("crs_whitelist", []));
        self.keyinfo["tma_whitelist"] = set(self.keyinfo.get("tma_whitelist", []));
    
    def chk_tma(self, tg, logger = print):
        if not int(self.keyinfo.get("tw_count", 0)):
            return True;

        if len(self.keyinfo["tma_whitelist"]) < int(self.keyinfo["tw_count"]):
            self.keyinfo["tma_whitelist"].add(str(tg).lower());
            
            return self.upload();
        
        elif str(tg).lower() in self.keyinfo["tma_whitelist"]:
            return True;
        
        logger("Key is incompatible with TMA%s" % (tg,));
        return False;


    def chk_user(self, tg, logger = print):
        if not int(self.keyinfo.get("uw_count", 0)):
            return True;

        if len(self.keyinfo["user_whitelist"]) < int(self.keyinfo["uw_count"]):
            self.keyinfo["user_whitelist"].add(str(tg).lower());
            
            return self.upload();
        
        elif str(tg).lower() in self.keyinfo["user_whitelist"]:
            return True;

        logger("Key is incompatible with more than %s matric numbers" % (self.keyinfo["uw_count"],));
        return False;
    
    def chk_crs(self, tg, logger = print):
        if not int(self.keyinfo.get("cw_count", 0)):
            return True;

        if len(self.keyinfo["crs_whitelist"]) < int(self.keyinfo["cw_count"]):
            self.keyinfo["crs_whitelist"].add(str(tg).lower());
            
            return self.upload();
        
        elif str(tg).lower() in self.keyinfo["crs_whitelist"]:
            return True;

        logger("Key is incompatible with more than %s courses" % (self.keyinfo["cw_count"],));

        return False;
    

    def _serialize(self, obj):
        if isinstance(obj, set):
            return list(obj);

    def upload(self):
        data = json.dumps(self.keyinfo, default = self._serialize)
        try:
            write_keyfile(
                    str(
                        pathlib.Path(
                            self.kpath
                            ).joinpath(
                                ".%s" % (self.keyinfo,)
                                ).resolve()
                            ),
                    data,
                    );

            return update_file(str(self.keyinfo), data,self.updater);
        except BaseException:
            return False;


class KeyInfo(dict):
    def __init__(self, key, *pargs, **kwargs):
        self.key = str(key);
        super().__init__(*pargs, **kwargs);
    def __str__(self):
        return repr(self);

    def __repr__(self):
        return str(self.key);

    def __bool__(self):
        return bool(self.key);


class Base_headers(dict):
    def __init__(self, *pargs, **kwargs):
        global key;

        super().__init__(*pargs, **kwargs);

        self.key = key; 
        self["Authorization"] = "Bearer %s" % (self.key,);


def fetch_file(key, requester = libdogs.goto_page3):
    if not key:
        return None;

    hdrs = Base_headers();
    hdrs["Dropbox-API-Arg"] = json.dumps(
            {
                "path": "/%s" % (key,),
                }
            );

    res = requester("GET", download_url, headers = hdrs);
    
    if not res:
        return res;

    return res.text;


def update_file(key, data, updater = libdogs.goto_page3):
    hdrs = Base_headers();
    hdrs["Dropbox-API-Arg"] = json.dumps(
            {
                "path": "/%s" % (key,),
                }
            );

    res = updater("GET", download_url, headers = hdrs);
    
    if not res:
        return res;

    keyobj = json.loads(res.text);
    
    keyobj.update(json.loads(data));

    keyobj["mtime"] = int(keyobj.get("mtime", -1)) + 1;
    hdrs["Dropbox-API-Arg"] = json.dumps(
            {
                "path": "/%s" % (key,),
                "mode": "overwrite",
                "mute": True,
                }
            );
    hdrs["Content-Type"] = "application/octet-stream";

    return updater("POST", upload_url, headers = hdrs, data = json.dumps(keyobj));


def write_file(key, data, requester = libdogs.goto_page3):
    hdrs = Base_headers();

    hdrs["Dropbox-API-Arg"] = json.dumps(
            {
                "path": "/%s" % (key,),
                "mode": "overwrite",
                "mute": True,
                }
            );

    hdrs["Content-Type"] = "application/octet-stream";

    return requester("POST", upload_url, headers = hdrs, data = str(data));


def ZipFd(requester = libdogs.goto_page3, zfname = "zipfile"):
    zf_str = fetch_file(zfname, requester);

    if not zf_str:
        return zf_str;
    
    zdata = json.loads(zf_str);

    class _Zdata:
        @property
        def name(self):
            return zdata["name"];
        
        @property
        def nbits(self):
            return int(zdata.get("nbits", 128));

        @property
        def password(self):
            return zdata["password"];
    
    return _Zdata();


def list_folder(key, requester = libdogs.goto_page3):
    hdrs = Base_headers();

    hdrs["Content-Type"] = "application/json";

    data = {
            "path": str(key),
            "recursive": False,
            "include_media_info": False,
            "include_deleted": False,
            "include_has_explicit_shared_members": False,
            "include_mounted_folders": False,
            "include_non_downloadable_files": False,
            }; 

    res = requester("POST", list_url, headers = hdrs, data = json.dumps(data));
    
    if not res:
        return res;

    return json.loads(res.text);


def Updates(requester = libdogs.goto_page3, ufname = "update"):
    u_str = fetch_file(ufname, requester);

    if not u_str:
        return u_str;
    
    udata = json.loads(u_str);

    class _Udata:
        @property
        def version(self):
            return int(udata["version"]);
        
        @property
        def urls(self):
            return udata["urls"];

    
    return _Udata();


class Cmds:
    def extend_key(self, argv):
        # the default command
        parser = libdogs.DogCmdParser ();
        parser.add_argument("key", action = libdogs.AppendList, help =
            "keys to remove", nargs = "+");

        parser.add_argument("--users", help = "Number of users to restrict a key to", type = int);

        parser.add_argument("--tmas", type = int, help = "Number of tma to restrict a key to");

        parser.add_argument("--courses", type = int, help = "Number of courses to restrict a key to");

        parser.add_argument("--count", help = "Number of keys", default = 1, type =
                int);

        args = parser.parse_args(argv);

        for i in args.key:
            keyobj = fetch_keyinfo(i);
            
            if args.users:
                keyobj["uw_count"] = int(keyobj.get("uw_count", 0)) + args.users;

            if args.courses:
                keyobj["cw_count"] = int(keyobj.get("cw_count", 0)) + args.courses;

            if args.tmas:
                keyobj["tw_count"] = int(keyobj.get("tw_count", 0)) + args.tmas;
            
            # must pass
            while not write_file(str(keyobj), json.dumps(keyobj)):
                pass;

            print(keyobj, "extended successfully");


    def add(self, argv):
        # the default command
        parser = libdogs.DogCmdParser ();
        parser.add_argument("--users", help = "Number of users to restrict a key to", type = int);

        parser.add_argument("--tmas", type = int, help = "Number of tma to restrict a key to");

        parser.add_argument("--courses", type = int, help = "Number of courses to restrict a key to");

        parser.add_argument("--count", help = "Number of keys", default = 1, type =
                int);

        args = parser.parse_args(argv);

        for i in range(args.count):
            keyobj = gen_key_with_epoch(i); #will always succeed, no checks needed
            
            keyobj["ts"] = 0;

            if args.users:
                keyobj["uw_count"] = args.users;

            if args.courses:
                keyobj["cw_count"] = args.courses;

            if args.tmas:
                keyobj["tw_count"] = args.tmas;
            
            # must pass
            while not write_file(str(keyobj), json.dumps(keyobj)):
                pass;

            print(keyobj);


    def ls(self, argv):
        parser = libdogs.DogCmdParser ();
        parser.add_argument("--file", action = libdogs.AppendList, help =
            "keys to list", nargs = "+", dest = "key", required = False);

        parser.add_argument("-l", "--long", action = "store_true", help =
            "print long output", dest = "long");

        parser.add_argument("--human-readable", action = "store_true", help =
            "print human readable long output", dest = "hread");

        args = parser.parse_args(argv);
        # "/" returns and error, use an empty string
        dt = list_folder("");

        if not dt:
            print(dt.text);
            return None;

        if not args.key:
            args.key = [];
            for key in dt["entries"]:
                st = "%s" % (key["path_display"],);
                if args.long:
                    st += "    %s" % (key["server_modified"],);
                    if args.hread:
                        st += "    %s MiB" % (math.ceil(int(key["size"]) / 2**20),);
                    else:
                        st += "    %s KiB" % (math.ceil(int(key["size"]) / 2**10),);

                print(st);

        else:
            for key in dt["entries"]:
                try:
                    idx = args.key.index(key["name"]);

                except ValueError:
                    continue;

                st = "%s" % (key["path_display"],);
                if args.long:
                    st += "    %s" % (key["server_modified"],);
                    if args.hread:
                        st += "    %s MiB" % (math.ceil(int(key["size"]) / 2**20),);
                    else:
                        st += "    %s KiB" % (math.ceil(int(key["size"]) / 2**10),);

                print(st);

                args.key.pop(idx);

        for key in args.key:
            print("error: no such file or folder %s" % (key,));

        print("\nDone.");

    
    def remove(self, argv):
        parser = libdogs.DogCmdParser ();
        parser.add_argument("key", action = libdogs.AppendList, help =
            "keys to remove", nargs = "+");

        args = parser.parse_args(argv);
        
        for key in args.key:
            res = rm_key(key);
            if not res:
                print("cant't remove key %s\n%s" % (key, res.text));
            else:
                print("removed key %s" % (key,));

        print("\nDone.");

    
    def add_file(self, argv):
        parser = libdogs.DogCmdParser ();
        parser.add_argument("file", action = libdogs.AppendList, help =
            "file to add", nargs = "+");

        parser.add_argument("--stdin", "-st", help =
            "read from stdin", dest = "stdin", action = "store_true");

        args = parser.parse_args(argv);
        
        if args.stdin:
            dt = sys.stdin.read();
            res = write_file(args.file[0], dt);
            if not res:
                print("write error:", res.text);
            else:
                print("Done.");
        
        else:
            for fi in args.file:
                dt = libdogs.read_file_text(fi);
                if not dt:
                    print("no such file", fi);

                else:
                    res = write_file(fi, dt);
                    if not res:
                        print("could not write file", fi);
                        print(res.text, "\n");
                    else:
                        print("file", fi, "written");
        
    def add_json(self, argv):
        parser = libdogs.DogCmdParser ();
        parser.add_argument("file", help =
            "file to write");

        args,rest = parser.parse_known_args(argv);

        dt = {};

        # we process =-delimited key-value pairs in argv
        for arg in rest:
            tg = arg.split("=", 1);
            # an un-delimited argument is a key with empty string as value
            value = tg[-1] if len(tg) > 1 else "";
            
            if tg[0] in dt:
                if not isinstance(dt[tg[0]], list):
                    dt[tg[0]] = [dt[tg[0]]];
                
                dt[tg[0]].append(value);

            else:
                dt[tg[0]] = value;
        
        
        res = write_file(args.file, json.dumps(dt));
        if not res:
            print("can't write file", args.file);
        else:
            print("Done.");

    def dump(self, argv):
        parser = libdogs.DogCmdParser ();
        parser.add_argument("key", action = libdogs.AppendList, help =
            "keys to dump", nargs = "+");

        args = parser.parse_args(argv);

        for key in args.key:
            dt = fetch_file(key);
            print("\n\n%s: %s" % (key, "" if dt else "error"));
            print(dt if dt else dt.text);
            print("\n--------------------");

        print("\nDone.");

    def reset(self, argv):
        parser = libdogs.DogCmdParser ();
        parser.add_argument("key", action = libdogs.AppendList, help =
            "keys to reset", nargs = "+");

        args = parser.parse_args(argv);

        for key in args.key:
            dt = dealloc_key(key);
            if dt:
                print("%s: reset successful" % (key,));
            else:
                print("%s: %s" % (key, dt.text));

        print("\nDone.");


    def dump_json(self, argv):
        parser = libdogs.DogCmdParser ();
        parser.add_argument("key", action = libdogs.AppendList, help =
            "keys to dump", nargs = "+");

        args = parser.parse_args(argv);

        for key in args.key:
            dt = fetch_keyinfo(key);
            print("\n\n%s: %s" % (key, "" if dt else "error"));
            print(json.dumps(dt, indent = 4) if dt else dt.text);
            print("\n--------------------");

        print("\nDone.");


    def find(self, argv):
        # can exec a select number of other commands in this object. Similar to unix's 'find'
        print("command currently unavailable");

    def edit_json(self, argv):
        parser = libdogs.DogCmdParser ();
        parser.add_argument("file", help =
            "file to write");

        args,rest = parser.parse_known_args(argv);

        dt1 = fetch_keyinfo(args.file);
        dt = {};

        if not isinstance(dt, KeyInfo):
            return self.add_json(argv);

        # we process =-delimited key-value pairs in argv
        for arg in rest:
            tg = arg.split("=", 1);
            # an un-delimited argument is a key with empty string as value
            value = tg[-1] if len(tg) > 1 else "";
            
            if tg[0] in dt:
                if not isinstance(dt[tg[0]], list):
                    dt[tg[0]] = [dt[tg[0]]];
                
                dt[tg[0]].append(value);

            else:
                dt[tg[0]] = value;
        
        dt1.update(dt);
        res = write_file(args.file, json.dumps(dt1));
        if not res:
            print("can't write file", args.file);
        else:
            print("Done.");


if __name__ == "__main__":

    kparser = argparse.ArgumentParser(fromfile_prefix_chars='@');
    cmds = Cmds();
    choices = [ cmd for cmd in dir(cmds) if re.fullmatch(r'[^_]\w*', cmd) ]
    kparser.add_argument("cmd", choices = choices);

    args,rest = kparser.parse_known_args();
    getattr(cmds, args.cmd)(rest);




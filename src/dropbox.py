import json, re
import time
import math
import sys
import argparse
import libdogs
import requests

upload_url = "https://content.dropboxapi.com/2/files/upload";

download_url = "https://content.dropboxapi.com/2/files/download";

delete_url = "https://api.dropboxapi.com/2/files/delete";

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
    return KeyInfo(time.time());


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

    keyobj["ts"] = int(keyobj.get("ts", -1)) + 1;
    keyobj["mtime"] = int(keyobj.get("mtime", -1)) + 1;
    
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
        rkinfo = dropbox.fetch_keyinfo(str(self.keyinfo));
        if rkinfo and rkinfo.get("mtime", 0) > self.keyinfo.get("mtime", 0):
            self.keyinfo.update(rkinfo);
        
        self.keyinfo["user_whitelist"] = set(self.keyinfo.get("user_whitelist", []));
        self.keyinfo["crs_whitelist"] = set(self.keyinfo.get("crs_whitelist", []));
        self.keyinfo["tma_whitelist"] = set(self.keyinfo.get("tma_whitelist", []));
    
    def chk_tma(self, tg, logger = print):
        if not int(self.keyinfo.get("tw_count", 0)):
            return True;

        if len(self.keyinfo["tma_whitelist"]) < int(self.keyinfo["tw_count"]):
            self.keyinfo["tma_whitelist"].add(tg);
            
            return self.upload();
        
        elif tg in self.keyinfo["tma_whitelist"]:
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
                            self.path
                            ).joinpath(
                                ".%s" % (self.keyinfo,)
                                ).resolve()
                            ),
                    data,
                    );

            return dropbox.update_file(self, data,self.updater);
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

        @property
        def exec(self):
            return udata["exec"];
    
    return _Udata();


class Cmds:
    def add(self, argv):
        # the default command
        kparser = libdogs.DogCmdParser ();
        kparser.add_argument("--paid", "--no-whitelist", action = "store_false",
        help = "a key restricted by a whitelist", default = True, dest =
        "whitelisted");

        kparser.add_argument("-wc", "--max_whitelist", type = int, default = 2,
        help = "max users in whitelist", dest = "wc");

        kparser.add_argument("--unrestricted", action = "store_true",
        help = "a key unrestricted");

        kparser.add_argument("--pro", action = "store_true",
        help = "Any tma number can be submitted (experimental)");
        
        kparser.add_argument("--owner", help = "A unique ID of the owner of the key");

        kparser.add_argument("--count", help = "Number of keys", default = 1, type =
                int);

        for i in range(args.count):
            keyobj = gen_key_with_epoch(i); #will always succeed, no checks needed
            
            o_info = fetch_keyinfo(args.owner);

            if args.whitelisted:
                keyobj["whitelist"] = [];
                keyobj["max_wlist"] = args.wc;

                if args.owner:
                    if o_info and o_info.get("wlist_keys", []):
                        raise KeyError(
                                "A single owner %s can't have more than one whitelist key" %
                                (args.owner,)
                                );
                    else:
                        o_info = KeyInfo(args.owner);

                    o_info["wlist_keys"] = [str(keyobj)];
                    keyobj["owner"] = str(o_info);



            keyobj["tmano"] = libdogs.TMANO_STRICT if not args.pro else libdogs.TMANO_LAX;

            keyobj["ts"] = 0;

            try:
                if o_info:
                    res = put_key(o_info);
                    if not res:
                        print("\n%s\n" % (res.text,));
                        raise Exception();

                res = put_key(keyobj);
                if not res:
                    print("\n%s\n" % (res.text,));
                    raise Exception();

                print(keyobj);
            except Exception:
                print ("failure generating key");

    def rm(self, argv):
        parser = libdogs.DogCmdParser ();
        parser.add_argument("key", action = libdogs.AppendList, help =
            "keys to remove", nargs = "+");

        args = parser.parse_args(argv);
        
        for key in args.key:
            res = rm_key(args.rm);
            if not res:
                print("cant't remove key %s\n%s" % (args.rm, res.text));

        print("\nDone.");


    def add_json(self, argv):
        pass;

    def dump(self, argv):
        parser = libdogs.DogCmdParser ();
        parser.add_argument("key", action = libdogs.AppendList, help =
            "keys to dump", nargs = "+");

        args = parser.parse_args(argv);

        for key in args.key:
            print("\n\n%: --|" % (key,), json.dumps(fetch_keyinfo(key)));
            print("\n\n--------------------");

        print("\nDone.");


    def find(self, argv):
        # can exec a select number of other commands in this object. Similar to unix's 'find'
        pass;

    def edit(self, argv):
        pass;


if __name__ == "__main__":

    kparser = argparse.ArgumentParser(fromfile_prefix_chars='@');


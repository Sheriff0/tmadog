import requests, json, re
import time
import math
import sys
import argparse
import libdogs

upload_url = "https://content.dropboxapi.com/2/files/upload";

download_url = "https://content.dropboxapi.com/2/files/download";

delete_url = "https://api.dropboxapi.com/2/files/delete";

key = "zxK60VpMtmwAAAAAAAAAAZ76lD62i4GvL5SxC9ZgkQpIrpV4cReqSh0-SoujeAtZ";

MAX_WAIT_SEC = 10;


def gen_whitelisted_key(nlist):
    hdrs = Base_headers();
    key = math.trunc(time.time());
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
    return KeyInfo(math.trunc(time.time()));


def fetch_keyinfo(key):
    if not key:
        return None;

    hdrs = Base_headers();
    hdrs["Dropbox-API-Arg"] = json.dumps(
            {
                "path": "/%s" % (key,),
                }
            );

    res = libdogs.goto_page3("GET", download_url, headers = hdrs);
    
    if not res:
        return res;

    return KeyInfo(key, json.loads(res.text));



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

    keyobj["mtime"] = math.trunc(time.time());
    hdrs["Dropbox-API-Arg"] = json.dumps(
            {
                "path": "/%s" % (keyobj,),
                "mode": "overwrite",
                "mute": True,
                }
            );
    hdrs["Content-Type"] = "application/octet-stream";

    return libdogs.goto_page3("POST", upload_url, headers = hdrs, data = json.dumps(keyobj));

    
def update_key(key):
    hdrs = Base_headers();
    hdrs["Dropbox-API-Arg"] = json.dumps(
            {
                "path": "/%s" % (key,),
                }
            );

    res = libdogs.goto_page3("GET", download_url, headers = hdrs);
    
    if not res:
        return res;

    keyobj = json.loads(res.text);
    
    keyobj.update(key);

    keyobj["mtime"] = math.trunc(time.time());
    hdrs["Dropbox-API-Arg"] = json.dumps(
            {
                "path": "/%s" % (key,),
                "mode": "overwrite",
                "mute": True,
                }
            );
    hdrs["Content-Type"] = "application/octet-stream";

    return libdogs.goto_page3("POST", upload_url, headers = hdrs, data = json.dumps(keyobj));


def alloc_key(key):
    hdrs = Base_headers();
    hdrs["Dropbox-API-Arg"] = json.dumps(
            {
                "path": "/%s" % (key,),
                }
            );

    res = libdogs.goto_page3("GET", download_url, headers = hdrs);
    
    if not res:
        return res;

    keyobj = json.loads(res.text);
    
    if "ts" in keyobj and keyobj["ts"]:
        return False;

    if isinstance(key, dict):
        keyobj.update(key);

    keyobj["ts"] = math.trunc(time.time());
    keyobj["mtime"] = keyobj["ts"];

    hdrs["Dropbox-API-Arg"] = json.dumps(
            {
                "path": "/%s" % (key,),
                "mode": "overwrite",
                "mute": True,
                }
            );

    hdrs["Content-Type"] = "application/octet-stream";

    res = libdogs.goto_page3("POST", upload_url, headers = hdrs, data = json.dumps(keyobj));

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



if __name__ == "__main__":

    kparser = argparse.ArgumentParser(fromfile_prefix_chars='@');

    kparser.add_argument("--paid", "--no-whitelist", action = "store_false",
    help = "a key restricted by a whitelist", default = True, dest =
    "whitelisted");

    kparser.add_argument("-wc", "--max_whitelist", type = int, default = 5,
    help = "max users in whitelist", dest = "wc");

    kparser.add_argument("--unrestricted", action = "store_true",
    help = "a key unrestricted");

    kparser.add_argument("--pro", action = "store_true",
    help = "Any tma number can be submitted (experimental)");
    
    kparser.add_argument("--owner", help = "A unique ID of the owner of the key");

    kparser.add_argument("--dump", help = "A key to dump");

    kparser.add_argument("--rm", help = "A key to delete");

    kparser.add_argument("--count", help = "Number of keys", default = 1, type =
            int);

    kparser.add_argument("--put", help = "A key to force");

    args = kparser.parse_args();

    if args.rm:
        res = rm_key(args.rm);
        if not res:
            print("cant't remove key %s\n%s" % (args.rm, res.text));
        else:
            print("removed %s" % (args.rm,));
        sys.exit(0);

    if args.rm:
        res = rm_key(args.rm);
        if not res:
            print("cant't remove key %s\n%s" % (args.rm, res.text));
        else:
            print("removed %s" % (args.rm,));
        sys.exit(0);


    if args.dump:
        print(json.dumps(fetch_keyinfo(args.dump)));
        sys.exit(0);

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

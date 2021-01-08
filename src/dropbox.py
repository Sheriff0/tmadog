import requests, json
import time
import math
import libdogs

upload_url = "https://content.dropboxapi.com/2/files/upload";

download_url = "https://content.dropboxapi.com/2/files/download";

key = "zxK60VpMtmwAAAAAAAAAAZ76lD62i4GvL5SxC9ZgkQpIrpV4cReqSh0-SoujeAtZ";

MAX_WAIT_SEC = 10;


def gen_key_with_epoch():
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

    res = libdogs.goto_page3("POST", upload_url, headers = hdrs, data = json.dumps({"ts": 0}));
    
    if not res:
        return False;

    return key;


def is_allocatable(key):
    hdrs = Base_headers();
    hdrs["Dropbox-API-Arg"] = json.dumps(
            {
                "path": "/%s" % (key,),
                }
            );

    res = libdogs.goto_page3("GET", download_url, headers = hdrs);
    
    if not res:
        return None;

    keyobj = json.loads(res.text);
    
    return "ts" not in keyobj or not keyobj["ts"];


def alloc_key(key):
    hdrs = Base_headers();
    hdrs["Dropbox-API-Arg"] = json.dumps(
            {
                "path": "/%s" % (key,),
                }
            );

    res = libdogs.goto_page3("GET", download_url, headers = hdrs);
    
    if not res:
        return False;

    keyobj = json.loads(res.text);
    
    if "ts" in keyobj and keyobj["ts"]:
        return False;

    keyobj = {};
    keyobj["ts"] = math.trunc(time.time());
    hdrs["Dropbox-API-Arg"] = json.dumps(
            {
                "path": "/%s" % (key,),
                "mode": "overwrite",
                "mute": True,
                }
            );
    hdrs["Content-Type"] = "application/octet-stream";

    res1 = libdogs.goto_page3("POST", upload_url, headers = hdrs, data = json.dumps(keyobj));

    if not res1:
        return False;

    return keyobj["ts"];


class Base_headers(dict):
    def __init__(self, *pargs, **kwargs):
        global key;

        super().__init__(*pargs, **kwargs);

        self.key = key; 
        self["Authorization"] = "Bearer %s" % (self.key,);



if __name__ == "__main__":

    key = gen_key_with_epoch();
    if key:
        print(key);
    else:
        print("can't generate key");

import requests, json

url = "https://content.dropboxapi.com/2/files/upload";

key = "zxK60VpMtmwAAAAAAAAAAZ76lD62i4GvL5SxC9ZgkQpIrpV4cReqSh0-SoujeAtZ";


info = {
        "path": "/tmadog/keyfile",
        "mode": "overwrite",
        "mute": True,
        };

headers = {
        "Authorization": "Bearer %s" % (key,),
        "Dropbox-API-Arg": json.dumps(info),
        "Content-Type": "application/octet-stream"

        };

empty = {};

res = requests.post(url, headers = headers, data = json.dumps(empty));

print("created an empty key file at %s" % (info["path"],));

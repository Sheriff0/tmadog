import requests
import re

def fill_submit (html, url, session = None, idx = 0, **data):

    tform = re.findall (r'<form.+?</form>', html, re.DOTALL | re.MULTILINE |
            re.IGNORECASE)[idx]

    targs = {}

    targs['method'] = re.findall(r'<form.+?method.*?=.*?(?:"|\')(.*?)(?:"|\')', tform,
            re.DOTALL | re.MULTILINE)[0].upper ()

    targs['url'] = re.findall(r'<form.+?action.*?=.*?(?:"|\')(.*?)(?:"|\')', tform,
            re.DOTALL | re.MULTILINE)[0]

    if len (targs['url']) == 0 :
        targs['url'] = url

    else:
        targs['url'] = re.sub (url.split ('/')[-1], targs['url'], url)

    ifields = re.findall(r'<input.+?name.*?=.*?(?:"|\')(.*?)(?:"|\')', tform, re.DOTALL | re.MULTILINE)

    ifields += re.findall(r'<button.+?name.*?=.*?(?:"|\')(.*?)(?:"|\')', tform, re.DOTALL | re.MULTILINE)

    targs['data'] = { f: None for f in ifields }

    targs['data'].update (**{ f: data[f] for f in data if f in ifields })

    for k in targs['data']:

        if targs['data'][k] is None :

            r = input ('Pls fill {k}:\n\t--> '.format(**{'k': k}))
            if r.startswith(('None', 'no', 'null')):
                return False
            else:
                targs['data'][k] = r

    if targs['method'] in ('GET', 'get'):
        targs['params'] = targs['data']
        targs['data'] = None

    if session is not None and session is isinstance (session, requests.Session):
        treq = session.prepare_request (requests.Request(**targs))

        return session.send (treq)

    else:

        return requests.Request(**targs).prepare ()


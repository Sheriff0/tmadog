import requests
import re

def fill_submit (html, url, idx = 0, nonstdtags = [] , session = None, **data):

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

    ifieldp = r'.+?name.*?=.*?(?:"|\')(.*?)(?:"|\')'

    ifields = re.findall(r'<\s*input'+ifieldp, tform, re.DOTALL | re.MULTILINE)

    if len (nonstdtags) > 0 :
        ifields += [ f for farr in [ re.findall(r'<\s*' + i +
            ifieldp, tform, re.DOTALL | re.MULTILINE) for i in nonstdtags if not re.match ('input',
                i, re.IGNORECASE) ] for f in farr if f not in ifields]

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

        return requests.Request(**targs)


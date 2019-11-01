import requests
import re
from dogs.html_utils import uncomment_html, txtnode_to_name_attr


#def fill_radio ():

#def fill_checkbox ():

def fill_form (html, url, idx = 0, nonstdtags = [] , session = None, **data):
    html = uncomment_html (html)

    tform = re.findall (r'<form.+?</form>', html, re.DOTALL | re.MULTILINE |
            re.IGNORECASE)[idx]

    targs = {}

    targs['method'] = re.findall(r'<form.+?method.*?=.*?(?:"|\')(.*?)(?:"|\')', tform,
            re.DOTALL | re.MULTILINE)[0].upper ()

    targs['url'] = re.findall(r'<form.+?action\s*=\s*(?:"|\')(.*?)(?:"|\')', tform,
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

    tnodes = list (data.keys())
    names = txtnode_to_name_attr (tform, tnodes)

    targs['data'].update (**{ names[i] : data[tnodes[i]] for i in range (len
        (names)) if
        names[i] is not None and names[i] in ifields })

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

#def form_type ():


#def click_form ():

#def click_link ():

def click (html, ltext, idx = 0, session = None):
    tagcap = r'<\s*(?P<tag>\b\w+\b).+?>\s*'+ ltext + r'\s*<\s*/\1\s*>'
    for i, m in enumerate (re.finditer(tagcap, htm, re.MULTILINE)):
        if i == idx:
            break

    if re.fullmatch ('button', m.group ('tag'), flags = re.IGNORECASE):
        tform 
    elif re.fullmatch ('a', m.group ('tag'), flags = re.IGNORECASE):



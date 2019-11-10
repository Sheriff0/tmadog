import requests
import re
from dog_html_utils import uncomment_html, txtnode_to_name_attr, txtnode_to_value_attr

#__all__ = ['click', 'fill_form', 'getdef_value']

NO_TXTNODE_KEY = 0b0001
NO_TXTNODE_VALUE = 0b0010

LastForm = {}

#def fill_radio ():

#def fill_checkbox ():

def undo_if_none (t):
        t, v = t
        if not v:
            return t
        else:
            return v

def getdef_value (form, t, fb = False):
    m = re.search (r'<\s*.+?name\s*=\s*(\'|")(?P<name>' + t + r')\1.*?>', form)
    if isinstance(m, re.Match):
        m = re.search (r'value\s*=\s*(\'|")(?P<value>.*?)\1.*?>', m.group(0))
    if isinstance (m, re.Match):
        return m.group('value')
    else:
        if fb:
            return t
        else:
            return None


def fill_form (html, url, flags, idx = 0, nonstdtags = [], **kwargs):
    html = uncomment_html (html)

    data = kwargs.pop('data', {})

    tform = re.findall (r'<form.+?</form>', html, re.DOTALL | re.MULTILINE |
            re.IGNORECASE)[idx]

    targs = {}
    
    kwargs.pop('method', None)

    targs['method'] = re.findall(r'<form.+?method.*?=.*?(?:"|\')(.*?)(?:"|\')', tform,
            re.DOTALL | re.MULTILINE)[0].upper ()


    targs['url'] = re.findall(r'<form.+?action\s*=\s*(?:"|\')(.*?)(?:"|\')', tform,
            re.DOTALL | re.MULTILINE)[0]

    if len (targs['url']) == 0 :
        targs['url'] = url

    else:
        targs['url'] = re.sub (url.split ('/')[-1], targs['url'], url)

    ifieldp = r'.+?name.*?=.*?(?:"|\')(.*?)(?:"|\')'

    ifields = list (set (re.findall(r'<\s*input'+ifieldp, tform, re.DOTALL |
        re.MULTILINE)))

    if len (nonstdtags) > 0 :
        ifields += [ f for farr in [ re.findall(r'<\s*' + i +
            ifieldp, tform, re.DOTALL | re.MULTILINE) for i in nonstdtags if not re.match ('input',
                i, re.IGNORECASE) ] for f in farr if f not in ifields]

    targs['data'] = { f: None for f in ifields }

    if flags  == (NO_TXTNODE_KEY | NO_TXTNODE_VALUE):
        targs['data'].update (**{k: data[k] for k in data if k in targs['data'] })
    
    else:
        if not flags & NO_TXTNODE_VALUE:
            ttuple = [ (k, data[k]) for k in data ]
            tnodes = [txtnode for k,txtnode in ttuple ]
            values = txtnode_to_value_attr (tform, tnodes)
            for i, v1 in enumerate (values):
                k,v0 = ttuple[i]
                if v1:
                    targs['data'][k] = v1
                else:
                    targs['data'][k] = v0

        if not flags & NO_TXTNODE_KEY:
            tnodes = list (data.keys())
            names = txtnode_to_name_attr (tform, tnodes)

            targs['data'].update (**{ names[i] : data[tnodes[i]] for i in range
                (len (names)) if
        names[i] is not None and names[i] in ifields })


    for k in targs['data']:

        if targs['data'][k] is None :
            r = getdef_value (tform, k, None)
            if not r:
                r = ''
            
            targs['data'][k] = r

    kwargs.pop('method', None)

    LastForm = targs['data']

    if targs['method'] in ('GET', 'get'):
        kwargs.pop('params', None)
        targs['params'] = targs['data']
        targs['data'] = None
    

    session = kwargs.pop('session', None)

    if isinstance (session, requests.Session):
        treq = session.prepare_request (requests.Request(**targs, **kwargs))

        return session.send (treq)

    else:

        return requests.Request(**targs, **kwargs)

#def form_type ():


#def click_form ():

#def click_link ():


def click (html, ltext, url, idx = 0, **kwargs):
    tagcap = r'<\s*(?P<tag>\ba\b|(?:\bbutton\b)).*?>\W*?'+ ltext + r'\W*?<\s*/\1\s*>'
    m = None

    for i, m in enumerate (re.finditer(tagcap, html, re.IGNORECASE)):
        if i == idx:
            break

    if m is not None:
        if re.fullmatch ('button', m.group ('tag'), flags = re.IGNORECASE):
            return fill_form (html, url, NO_TXTNODE_KEY | NO_TXTNODE_VALUE, idx =
                idx, nonstdtags = ['button'], **kwargs)

        elif re.fullmatch ('a', m.group ('tag'), flags = re.IGNORECASE):
            turl = re.search (r'href\s*=\s*(\'|")(?P<href>.*?)\1', m.group
                (0), re.IGNORECASE).group('href')
            if len (turl):
                turl = re.sub (url.split ('/')[-1], turl, url)
            else:
                turl = url

            if 'session' in kwargs and isinstance (kwargs['session'], requests.Session):
                session = kwargs.pop('session')

                treq = session.prepare_request (requests.Request(method =
                'GET', url =
                turl, **kwargs))
                return session.send (treq) 
            else:
        
                return requests.Request(method = 'GET', url = turl, **kwargs)
    else:
        return None



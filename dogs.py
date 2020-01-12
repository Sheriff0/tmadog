import requests_html
import re
from urllib.parse import urljoin
import lxml

requests = requests_html.requests

re.Match = type (re.match (r'foo', 'foo'))

class FDict (lxml.html.FieldsDict):
    def __init__ (self, *a0, **a1):
        return super ().__init__ (*a0, **a1)

    def __len__ (self):
        return len (dict (self))
    

#__all__ = ['click', 'fill_form', 'getdef_value']

NO_TXTNODE_KEY = 0b0001
NO_TXTNODE_VALUE = 0b0010
DATAONLY = 0b0100
URLONLY = 0b1000
EXTRAS = 0b10000

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


def fill_form (
        html,
        url = 'https://machine.com/dir/file.ext',
        flags = NO_TXTNODE_VALUE | NO_TXTNODE_KEY,
        selector = 'form',
        idx = 0,
        **kwargs
        ):

    data = kwargs.pop('data', {})
    
    html = lxml.html.fromstring (html = html, base_url = url) if not isinstance (html,
            lxml.html.HtmlElement) else html

    tform = html.cssselect (selector)

    if not len (tform):
        raise TypeError ('No form found')
    else:
        tform = tform[idx]

    targs = {}
    
    targs['method'] = tform.method

    targs['url'] = urljoin (tform.base_url, tform.action)

    if flags & URLONLY:
        return targs['url']

    if flags & EXTRAS:
        for e in tform.__copy__().cssselect (':not(input)[name]'):
            tform.append (requests_html.HTML (html = '''<input name = "%s" value =
                "%s">''' % (e.get ('name'), e.get ('value', ''))).find ('input', first = True).element)

    ifields = FDict (tform.inputs)

    params = kwargs.pop('params', {})

    data.update (**params)

    if not flags & NO_TXTNODE_VALUE:
        # unwilling to make sense now. will probe later
        pass
    if not flags & NO_TXTNODE_KEY:
        # Handle cases like:
        # html = '<label> Name <input name = "nm"> </label>'
        # data = {'Name': 'Linus'}
        ## make:
        # data = {'nm': 'Linus'}
        pass

    ifields.update (**data)
    
    for k in ifields:

        if ifields[k] is None and not k in data:
            ifields[k] = ''
    
    targs['data'] = ifields

    if flags & DATAONLY:
        return targs['data']

    if targs['method'] in ('GET', 'get'):
        targs['params'] = ifields

        targs['data'] = None

    return targs

#def form_type ():


#def click_form ():

#def click_link ():


def click (html, ltext, url, selector = 'a, form', idx = 0, **kwargs):

    html = requests_html.HTML (html = html, url = url) if not isinstance (html,
            requests_html.HTML) else html
    m = html.find (selector, containing = ltext)
    if not len (m):
        return None
    else:
        m = m[idx]
    
    t = m.element.tag

    if t in ('form', 'FORM'):
        flags = kwargs.pop ('flags', NO_TXTNODE_KEY | NO_TXTNODE_VALUE)
        return fill_form (m.html, url, flags = flags, **kwargs)
    elif t in ('a', 'A'):
        flags = kwargs.pop ('flags', ~(URLONLY | DATAONLY))

        if flags & URLONLY:
            return urljoin (url, m.attrs['href'])
        elif flags & DATAONLY:
            return {}
        else:
            return {
                    'method': 'GET', 
                    'url': urljoin (url, m.attrs['href']),
                    'params': kwargs.get ('params', None),
                    'data': kwargs.get ('data', None)
                    }

    else:
        return None


import requests_html
import re
from urllib.parse import urljoin
import lxml

requests = requests_html.requests

re.Match = type (re.match (r'foo', 'foo'))

class FDict (lxml.html.FieldsDict):
    def __init__ (self, form, *a0, **a1):
        if isinstance (form, requests_html.Element):
            self.form_ref = form

        else:
            raise TypeError ('''Fdict: form must be instance of class
                    requests_html.HTML.''', type (form))

        return super ().__init__ (*a0, **a1)

    def __len__ (self):
        return len (dict (self))

    def copy (self):
        return dict (self)
    
    def resolve_key (self, s):

        if s.startswith ('['):
            ele = self.form_ref.find (
                    'input[placeholder="%s"]' % (s.strip ('[]'),),
                first = True
                )
            if not ele:
                raise KeyError ('%s does not exist in form' % (s,))
            
            s = ele.attrs['name']

        elif s.startswith ('<'):
            p_ele = self.form_ref.find (
                    'form *',
                    containing = s.strip ('<>'),
                    first = True
                    )
            if not p_ele:
                raise KeyError ('%s does not exist in form' % (s,))

            ele = p_ele.find ('input', first = True)

            s = ele.attrs['name']

        return s

    def update (self, E, **F):
        if getattr (E, 'keys', None):
            for k in E:
                v = E[k]
                k = self.resolve_key (k)
                self[k] = v
        else:
            for k, v in E:
                k = self.resolve_key (k)
                self[k] = v

        for k in F:
            v = F[k]
            k = self.resolve_key (k)
            self[k] = v

        return self




#__all__ = ['click', 'fill_form', 'getdef_value']

NO_TXTNODE_KEY = 0b0001
NO_TXTNODE_VALUE = 0b0010
FILL_RET_DATAONLY = 0b0100
URLONLY = 0b1000
FILL_FLG_EXTRAS = 0b10000

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
        data = {}
        ):

    
    s = html

    html = lxml.html.fromstring (html = s, base_url = url) 

    tform, s = html.cssselect (selector), requests_html.HTML (html = s).find (selector)

    if not len (tform):
        raise TypeError ('No form found')
    else:
        tform, s = tform[idx], s[idx]

    targs = {}
    
    targs['method'] = tform.method

    targs['url'] = urljoin (tform.base_url, tform.action)

    if flags & URLONLY:
        return targs['url']

    if flags & FILL_FLG_EXTRAS:
        for e in tform.__copy__().cssselect ('form button[name]'):
            tform.append (requests_html.HTML (html = '''<input name = "%s" value =
                "%s">''' % (e.get ('name'), e.get ('value', ''))).find ('input', first = True).element)

    ifields = FDict (s, tform.inputs)

    ifields.update (data)
    
    for k in ifields:

        if ifields[k] is None and not k in data:
            ifields[k] = ''
    
    targs['data'] = ifields

    if flags & FILL_RET_DATAONLY:
        return targs['data']

    if targs['method'] in ('GET', 'get'):
        targs['params'] = targs.pop ('data')

    return targs

#def form_type ():


#def click_form ():

#def click_link ():


def click (html, button, url, selector = 'a, form', idx = 0, **kwargs):

    html = requests_html.HTML (html = html, url = url) if not isinstance (html,
            requests_html.HTML) else html
    m = html.find (selector, containing = button)
    if not len (m):
        return None
    else:
        m = m[idx]
    
    t = m.element.tag

    if t in ('form', 'FORM'):
        flags = kwargs.pop ('flags', NO_TXTNODE_KEY | NO_TXTNODE_VALUE)
        return fill_form (m.html, url, flags = flags, **kwargs)

    elif t in ('a', 'A'):
        flags = kwargs.pop ('flags', ~(URLONLY | FILL_RET_DATAONLY))

        if flags & URLONLY:
            return urljoin (url, m.attrs['href'])
        elif flags & FILL_RET_DATAONLY:
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


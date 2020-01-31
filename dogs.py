import requests_html
import re
from urllib import parse
import lxml

requests = requests_html.requests

re.Match = type (re.match (r'foo', 'foo'))

class FDict (lxml.html.FieldsDict):
    def __init__ (self, form, *a0, **a1):
        self.form_ref = requests_html.HTML (html = form)

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

    tform = html.cssselect (selector)

    if not len (tform):
        raise TypeError ('No form found')
    else:
        tform = tform[idx]

    targs = {}
    
    targs['method'] = tform.method

    targs['url'] = parse.urljoin (tform.base_url, tform.action)

    if flags & URLONLY:
        return targs['url']

    if flags & FILL_FLG_EXTRAS:
        for e in tform.__copy__().cssselect ('form button[name]'):
            tform.append (requests_html.HTML (html = '''<input name = "%s" value = "%s">''' % 
                (e.get ('name'), e.get ('value', ''))).find ('input', first = True).element)

    ifields = FDict (lxml.html.tostring (tform, with_tail = False, encoding = 'unicode'), tform.inputs)

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


def click (html, url, button, selector = 'a, form', idx = 0, **kwargs):

    html = lxml.html.fromstring (html = html, base_url = url)

    x = html.cssselect (selector)
    
    c = -1

    for m in x:
        if re.match (m.text.strip (), button.strip (), flags = re.I):
            c += 1

        if c == idx:
            break

    if c != idx:
        return None
        
    t = m.tag

    if t in ('form', 'FORM'):
        flags = kwargs.pop ('flags', NO_TXTNODE_KEY | NO_TXTNODE_VALUE)
        return fill_form (lxml.html.tostring (m, with_tail = False, encoding = 'unicode'), url, flags = flags, **kwargs)

    elif t in ('a', 'A'):
        flags = kwargs.pop ('flags', ~(URLONLY | FILL_RET_DATAONLY))

        if flags & URLONLY:
            return parse.urljoin (url, m.get('href'))

        elif flags & FILL_RET_DATAONLY:
            return dict (
                    map (
                        lambda a: (a.split ('=')[0], parse.unquote_plus (a.split ('=')[-1])), 
                        parse.urlparse (parse.urljoin (url, m.get('href'))).query.split ('&')
                        )
                    )

        else:
            return {
                    'method': 'GET', 
                    'url': parse.urljoin (url, m.get('href')),
                    }

    else:
        return None


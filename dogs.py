import requests_html
import re
from urllib import parse
import lxml
import pdb

requests = requests_html.requests

re.Match = type (re.match (r'foo', 'foo'))

class FDict (lxml.html.FieldsDict):
    def __init__ (self, form, *a0, **a1):
        self.form_ref = requests_html.HTML (html = form)

        return super ().__init__ (*a0, **a1)

    def __len__ (self):
        return len (dict (self))

    def copy (self):
        return requests.structures.OrderedDict (self)
    
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



class AnyheadList:
    def __init__ (self, arr, svalue = None, sidx = None):
        self.garr = (x for x in arr)

        self._arr = {}

        self.sidx = sidx

        if not sidx or svalue == None:
            for i, v in enumerate (self.garr):

                if svalue != None and svalue == v:
                    self.sidx = i
                    break
                elif svalue == None:
                    self.sidx = i
                    svalue = v
                    break

                self._arr ['-' + str (i)] = v

        self.iidx = 0
        self._arr ['-' + str (self.sidx)] = svalue
        self._arr [str (self.iidx)] = svalue

        self.pidx = self.sidx + 1
        self.exhausted = False
    
    def __repr__ (self):
        strv = '['

        vgen = iter (self)
        
        try:
            strv += str (next (vgen))
        except StopIteration:
            return '[]'

        for v in vgen:
            strv += ', ' + str (v)
        
        return strv + ']'

    def __iter__ (self):
        idx = 0

        while True:
            try:
                yield self [idx]

            except IndexError:
                return

            idx += 1

    def __next__ (self):
        yield from self.__iter__ ()
    
    def origin (self):
        return self.Orderly (self._arr)

    def __setitem__ (self, idx, value):
        self [idx]
        self._arr [str (idx)] = value

    def __getitem__ (self, idx):
        idx = str (idx)
        if not self.exhausted and idx not in self._arr:
            while self.pidx != self.sidx:
                try:
                    self.iidx += 1
                    y = next (self.garr)
                    self._arr [str (self.iidx)] = y
                    self._arr ['-' + str (self.pidx)] = y
                    
                    self.pidx += 1

                    if int (idx) == self.iidx:
                        break

                except StopIteration:
                    self.iidx -= 1
                    self.pidx = 0
                    self.garr = iter (self.Orderly (self._arr))

            if self.pidx == self.sidx:
                self.exhausted = True

        elif self.exhausted and idx not in self._arr:
            raise IndexError (idx)

        return self._arr [idx]

    class Orderly:
        def __init__ (self, dict_arr):
            self.dict_arr = dict_arr

        def __iter__ (self):

            for k in sorted (self.dict_arr.keys ()):
                if re.fullmatch (r'-\d+', k):
                    yield self.dict_arr [k]
                else:
                    return

        def __next__ (self):
            yield from self.__iter__ ()

        def __setitem__ (self, idx, value):
            self.dict_arr ['-' + str (idx)] = value

        def __getitem__ (self, idx):

            return self.dict_arr ['-' + str (idx)]


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
        if re.match (button.strip (), m.text_content ().strip (), flags = re.I):
            c += 1

        if c == idx:
            break

    if c != idx:
        raise TypeError ('No such button %s found' % (button))
        
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
                        lambda a: (parse.unquote_plus (a.split ('=')[0]), parse.unquote_plus (a.split ('=')[-1])), 
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

def mkheader (url, ref = None):

    url = parse.urlparse (url)
    ref = parse.urlparse (ref) if ref else None
    headers = {
                'host': url.hostname,
                'origin': '%s://%s' % (url.scheme, url.hostname),
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                }

    if ref:
        headers ['referer'] = ref.geturl ()

    if ref and url.geturl ().split ('/')[0] == ref.geturl ().split ('/')[0]:
        headers ['sec-fetch-site'] = 'same-origin'
    elif ref and url.hostname.endswith (ref.hostname.split ('.', 1)[-1]):
        headers ['sec-fetch-site'] = 'same-site'
    elif not ref:
        headers ['sec-fetch-site'] = 'none'
    else:
        headers ['sec-fetch-site'] = 'cross-site'

    return headers

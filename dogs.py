import requests_html
import re
from urllib.parse import urljoin

requests = requests_html.requests

re.Match = type (re.match (r'foo', 'foo'))

#__all__ = ['click', 'fill_form', 'getdef_value']

NO_TXTNODE_KEY = 0b0001
NO_TXTNODE_VALUE = 0b0010
DATAONLY = 0b0100
URLONLY = 0b1000

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


def fill_form (html, url, flags, idx = 0, selector = 'form', **kwargs):

    data = kwargs.pop('data', {})
    
    html = requests_html.HTML (html = html, url = url) if not isinstance (html,
            requests_html.HTML) else html

    tform = html.find (selector)

    if not len (tform):
        return None
    else:
        tform = tform[idx]

    targs = {}
    
    targs['method'] = tform.element.method

    targs['url'] = urljoin (tform.url, tform.element.action)

    if flags & URLONLY:
        return targs['url']

    ifields = tform.element.fields

    params = kwargs.pop('params', {})

    data.update (**params)

    submit = { el.attrs['name']: el.attrs.get ('value', '') for el in tform.find ('[type=submit][name]') }

    # targs['data'].update (**{el.attrs['name']: el.attrs.get ('value', None) for
    #    el in tform.find ('form button[name]')}) # or maybe 'form :not(input)[name]'

    
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

    try:
        ifields.update (**data)
    except KeyError:
        return None
    
    targs['data'] = dict (ifields)

    targs['data'].update (**submit)

    for k in targs['data']:

        if targs['data'][k] is None and not k in data:
            targs['data'][k] = ''

    if flags & DATAONLY:
        return targs['data']

    if targs['method'] in ('GET', 'get'):
        targs['params'] = targs['data']
        targs['data'] = None
    
        return targs

#def form_type ():


#def click_form ():

#def click_link ():


def click (html, ltext, url, idx = 0, **kwargs):

    html = requests_html.HTML (html = html, url = url) if not isinstance (html,
            requests_html.HTML) else html
    m = html.find ('a, form', containing = ltext)
    if not len (m):
        return None
    else:
        m = m[idx]
    
    t = m.element.tag

    if t in ('form', 'FORM'):
        return fill_form (m, url, NO_TXTNODE_KEY | NO_TXTNODE_VALUE, **kwargs)
    elif t in ('a', 'A'):
        return {
                'method': 'GET', 
                'url': urljoin (url, m.attrs['href'])
                }

    else:
        return None


import re
import dogs.dogs as dogs

def login (session, url, ldata):
    index = session.get (url, headers = {'referer': url})

    index.raise_for_status()
    
    lpage = dogs.click (index.text, 'Take TMA3', url+'pad', idx = 0, headers = {
        'referer': url,
        }, 
        session = session)

    lpage.raise_for_status()

    propage = dogs.fill_form (lpage.text, lpage.request.url , 
            dogs.NO_TXTNODE_VALUE | dogs.NO_TXTNODE_KEY, 
            idx = 0, 
            nonstdtags = ['button'],
            headers = {
                'referer': lpage.url,
                'origin': url[0:-1],
                'cache-control': 'max-age=0'
                }, 
            data = ldata, 
            session = session
            )
    
    propage.raise_for_status()
    
    return propage


def select_tma (html, **tinfo):
    tinfo.setdefault('code', r'\w{3}\d{3}')
    tinfo.setdefault('title', r'\w.+?')
    tinfo.setdefault('tma', r'tma[1-3]')

    tinfo.setdefault('matno', r'nou\d{9}')

    tpat = r'>\s*(?P<code>' + tinfo['code'] + r')\s*<.+\bp\b.*?>\s*' + tinfo['title'] + r'\s*</p>.+?<form.+?value\s*=\s*(?:\'|")(?P=code)' + tinfo['matno'] + tinfo['tma'] + r'.+?</form>'
    
    return re.search (tpat, html, flags = re.DOTALL | re.MULTILINE | re.IGNORECASE)


def get_query (html):
    return dogs.getdef_value (html, 'qdescr')

def get_qid (html):
    return dogs.getdef_value (html, 'qid')

#def getatask (optdeque, nopt):
#    ataskimg = {
#            'matno': None,
#            'pwd': None,
#            'tmano': 1,
#            'file': None
#            }
#    for opt,v in optdeque.copy():
#

import re
import dogs
import requests
import collections
import sqlite3

QstDbT = collections.namedtuple ('QstDbT', 'qdescr, ans, nouid', defaults =
        [None, None])

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

def fetchtma (url, matno, tma , crscode, html, **kwargs):

    def fetcher ():
        res = session.post(req.url, data = req.data, headers =
            req.headers)
        res.raise_for_status ()
        m = get_query (res.text)
        if m:
            return (m, get_qid (res.text))
        else:
            raise requests.HTTPError ('Not a Question Page', res)


    session = kwargs.pop ('session', requests)

    headers = kwargs.pop ('headers', None)

    if matno and crscode and html:
        req = dogs.fill_form(html, url = url, flags = dogs.NO_TXTNODE_KEY |
                dogs.NO_TXTNODE_VALUE, idx=0, nonstdtags =['button'], headers =
                headers)
        v = ''
        for k in req.data:
            if re.search (r'nou\d{9}', req.data[k], flags = re.IGNORECASE):
                v = req.data[k]
                break

        v = re.sub (r'nou\d{9}', matno.upper(), v, flags = re.IGNORECASE)
        
        v = re.sub (r'\w{3}\d{3}(\D)', crscode.upper() + r'\1', v, count =
                    1, flags = re.IGNORECASE)

        v = re.sub (r'tma[1-3]', 'TMA' + str (tma), v, flags = re.IGNORECASE)
        req.data[k] = v
    else:
        raise requests.HTTPError ('Incomplete TMA details', requests.Response ())

    return fetcher

#def updatedb_courses ():

def updatedb_questions (db, data):

    repeats = 0
    
    conn = sqlite3.connect (db)
    
    try:
        conn.execute ('''SELECT * from questions;''')

    except sqlite3.OperationalError as err:
        if (re.search ('no\s+such\s+table', err.args[0], flags =
            re.IGNORECASE)):
            conn.execute ('''CREATE TABLE questions (dogid INTEGER PRIMARY KEY
                    AUTOINCREMENT, qdescr VARCHAR NOT NULL UNIQUE, ans VARCHAR,
                    nouid CHAR);''')
        else:
            print (err.args[0])
            conn.close ()
            return -1


    for datum in set (map ( 
        lambda t: QstDbT('+'.join (t.qdescr.strip ().split ()), t.ans, t.nouid), 
        data)):
        try:
            conn.execute ('''INSERT INTO questions (qdescr, ans, nouid)
                    VALUES (?, ?, ?);''', (datum.qdescr, datum.ans, datum.nouid))

        except sqlite3.IntegrityError:
            repeats += 1
        
        except sqlite3.OperationalError as err:
            print (err.args[0])
            conn.close ()
            return -1

    try:
        conn.commit ()

    except sqlite3.OperationalError as err:
        print (err.args[0])
        return conn

    conn.close()

    if repeats > 0:
        print ('%d questions repeated' % (repeats,))

    return None

import re
import dogs
import requests
import collections
import sqlite3
import hashlib

QstDbT = collections.namedtuple ('QstDbT', 'qdescr, ans, nouid, crscode')

#CrsDbT = collections.namedtuple ('CrsDbT', 'crscode, qid, answered', defaults = [False])

def login (session, url, **ldata):
    
    if not ldata:
        return -1

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

    def fetcher (url = None, headers = {}):
        url = url if url else req.url
        req.headers.update (**headers)
        res = session.post(url, data = req.data, headers =
            req.headers)
        res.raise_for_status ()
        m = dogs.fill_form (res.text, 'https://foo/foo.html', flags =
                dogs.NO_TXTNODE_KEY | dogs.NO_TXTNODE_VALUE | dogs.DATAONLY,
                data = { 'ans': None })
        if 'qdescr' in m:
            return m
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


#def update_hacktb (db, data):
#
#    repeats = 0
#    
#    conn = sqlite3.connect (db)
#
#    conn.row_factory = sqlite3.Row
#
#    cur = conn.cursor ()
#
#    ierr = None
#    
#    try:
#        cur.executescript ('''
#	CREATE TABLE IF NOT EXISTS hacktb (qref INTEGER NOT NULL UNIQUE
#        REFERENCES courses (cid), 
#        opta VARCHAR NOT NULL,
#        optb VARCHAR NOT NULL,
#        optc VARCHAR NOT NULL,
#        optd VARCHAR NOT NULL,
#        );
#                ''')
#
#    except sqlite3.OperationalError as err:
#        print ('create: ',err.args[0])
#        conn.close ()
#        return -1
#
#
#    qid, cid, = None, None
#
#    for datum in set (data):
#        try:
#            crsref = cur.execute ('''
#                    SELECT * FROM courses WHERE nouid = ? AND crscode = ?
#                    ;''', (datum['qid'], datum['crscode'].lower ())).fetchone ()
#            or {
#                    'cid': None,
#                    'crscode': datum['crscode'].lower (),
#                    'nouid': datum['qid'],
#                    'ready': False,
#                    'qid': None
#                    }
#
#
#            cur.execute ('''REPLACE INTO courses (cid, crscode, qid, ready,
#            nouid) VALUES
#                    (?, ?, ?, ?, ?)''', (
#                        crsref['cid']
#                        crsref['crscode'],
#                        crsref['qid'],
#                        crsref['ready'],
#                        crsref['nouid']
#                        ))
#
#            cid = cur.lastrowid
#
#            cur.execute ('''
#                    REPLACE INTO hacktb (qref, opta, optb, optc, optd) VALUES (?, ?,
#                    ?, ?, ?);
#                    ''', (
#                        cid,
#                        datum['opta'],
#                        datum['optb'],
#                        datum['optc'],
#                        datum['optd']
#                        ))
#
#        except sqlite3.IntegrityError as ierr:
#            
#            repeats += 1
#
#            dupq = cur.execute ('SELECT * FROM questions WHERE qdescr = ?', (datum.qdescr,)).fetchone ()
#
#            crsref = cur.execute (''' 
#                    SELECT * FROM courses WHERE (crscode = ? AND nouid = ? AND
#                    qid = ?) OR (qid = ? AND ready = ?) LIMIT 1
#                    ''', (
#                        datum.crscode,
#                        datum.nouid,
#                        dupq['dogid'],
#                        dupq['dogid'],
#                        False
#                        )).fetchone() or {
#                                'cid': None, 
#                                'qid': dupq['dogid'],
#                                'crscode': None,
#                                'ready': False,
#                                'nouid': None
#                                } 
#    
#            ansref = cur.execute ('''SELECT * FROM answers WHERE (qref =
#                    ? AND crsref = ?) OR qref = ?;''', (
#                        dupq['dogid'],
#                        crsref['cid'],
#                        dupq['dogid']
#                        )).fetchone () or {
#                                'ans': None, 
#                                'qref': None, 
#                                'crsref': None
#                                }
#
#            cur1 = conn.cursor ()
#
#            cur1.execute (''' 
#                    REPLACE INTO courses (cid, crscode, qid, ready, nouid)
#                    VALUES (?, ?, ?, ?, ?)
#                    ''', (
#                        crsref['cid'],
#                        datum.crscode or crsref['crscode'],
#                        crsref['qid'],
#                        ((ansref['ans'] or datum.ans) and (datum.nouid or
#                            crsref['nouid']) and (crsref['crscode'] or datum.crscode)) is not None,
#                        datum.nouid or crsref['nouid']
#                        ))
#
#            cid = cur1.lastrowid
#
#            cur.execute (''' 
#                    REPLACE INTO answers (ans, qref, crsref) VALUES (?,
#                    ?, ?)
#                    ''', (
#                        datum.ans or ansref['ans'],
#                        dupq['dogid'],
#                        cid
#                        ))
#        
#        except sqlite3.OperationalError as err:
#            print ('insert/replace: ', err.args[0])
#            conn.close ()
#            return -1
#
#
#    try:
#        conn.commit ()
#
#    except sqlite3.OperationalError as err:
#        print (err.args[0])
#        return conn
#
#    conn.close()
#
#    if repeats > 0:
#        print ('%d questions repeated' % (repeats,))
#
#    return None
#


def updatedb (db, data):

    repeats = 0
    
    conn = sqlite3.connect (db)

    conn.row_factory = sqlite3.Row

    cur = conn.cursor ()

    ierr = None
    
    try:
        cur.executescript ('''
	CREATE TABLE IF NOT EXISTS questions (dogid INTEGER PRIMARY KEY
		AUTOINCREMENT, qdescr VARCHAR NOT NULL UNIQUE);

	CREATE TABLE IF NOT EXISTS courses (cid INTEGER PRIMARY KEY
		AUTOINCREMENT, crscode CHAR(6) DEFAULT NULL, qid INTEGER NOT
                NULL REFERENCES questions (dogid) MATCH FULL ON DELETE CASCADE ON
                UPDATE CASCADE, ready BOOLEAN DEFAULT FALSE, nouid CHAR);

	CREATE TABLE IF NOT EXISTS answers (ans VARCHAR DEFAULT NULL, qref INTEGER
		NOT NULL REFERENCES questions (dogid) MATCH FULL ON DELETE
		CASCADE ON UPDATE CASCADE, crsref INTEGER UNIQUE DEFAULT NULL
		REFERENCES courses (cid) MATCH FULL ON DELETE CASCADE ON
		UPDATE CASCADE);
                ''')

    except sqlite3.OperationalError as err:
        print ('create: ',err.args[0])
        conn.close ()
        return -1


    qid, cid, = None, None

    for datum in set (map ( 
        lambda t: QstDbT(
            '+'.join (re.sub (r'\\[ntr]', ' ', t['qdescr'].strip ()).split ()), 
            '+'.join (re.sub(r'\W', ' ',t['ans'].strip()).split ()) if isinstance (t['ans'], str) else t['ans'], 
            t['qid'].strip() if isinstance (t['qid'], str) else t['qid'],
            t['crscode'].strip().upper() if isinstance (t['crscode'], str) else t['crscode']
            ), 
        data)):
        try:
            cur.execute ('''INSERT INTO questions (qdescr)
                    VALUES (?);''', (datum.qdescr,))

            qid = cur.lastrowid
            cid = None

            cur.execute ('''INSERT INTO courses (crscode, qid, ready,
            nouid) VALUES
                    (?, ?, ?, ?)''', (
                        datum.crscode,
                        qid,
                        (datum.ans and datum.crscode and datum.nouid) is not None,
                        datum.nouid
                        ))

            cid = cur.lastrowid

            cur.execute ('''
                    INSERT INTO answers (ans, qref, crsref) VALUES (?, ?,
                    ?);
                    ''', (
                        datum.ans,
                        qid,
                        cid
                        ))

        except sqlite3.IntegrityError as ierr:
            
            repeats += 1

            dupq = cur.execute ('SELECT * FROM questions WHERE qdescr = ?', (datum.qdescr,)).fetchone ()

            crsref = cur.execute (''' 
                    SELECT * FROM courses WHERE (crscode = ? AND nouid = ? AND
                    qid = ?) OR (qid = ? AND ready = ?) LIMIT 1
                    ''', (
                        datum.crscode,
                        datum.nouid,
                        dupq['dogid'],
                        dupq['dogid'],
                        False
                        )).fetchone() or {
                                'cid': None, 
                                'qid': dupq['dogid'],
                                'crscode': None,
                                'ready': False,
                                'nouid': None
                                } 
    
            ansref = cur.execute ('''SELECT * FROM answers WHERE (qref =
                    ? AND crsref = ?) OR qref = ?;''', (
                        dupq['dogid'],
                        crsref['cid'],
                        dupq['dogid']
                        )).fetchone () or {
                                'ans': None, 
                                'qref': None, 
                                'crsref': None
                                }

            cur1 = conn.cursor ()

            cur1.execute (''' 
                    REPLACE INTO courses (cid, crscode, qid, ready, nouid)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (
                        crsref['cid'],
                        datum.crscode or crsref['crscode'],
                        crsref['qid'],
                        ((ansref['ans'] or datum.ans) and (datum.nouid or
                            crsref['nouid']) and (crsref['crscode'] or datum.crscode)) is not None,
                        datum.nouid or crsref['nouid']
                        ))

            cid = cur1.lastrowid

            cur.execute (''' 
                    REPLACE INTO answers (ans, qref, crsref) VALUES (?,
                    ?, ?)
                    ''', (
                        datum.ans or ansref['ans'],
                        dupq['dogid'],
                        cid
                        ))
        
        except sqlite3.OperationalError as err:
            print ('insert/replace: ', err.args[0])
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

import re
import dogs
import requests
import collections
import sqlite3
import hashlib
import builtins

QstDbT = collections.namedtuple ('QstDbT', 'qdescr, ans, qid, crscode')

#CrsDbT = collections.namedtuple ('CrsDbT', 'crscode, qid, answered', defaults = [False])

def login (session, url, button = 'Login',**ldata):

    if not ldata:
        return -1
    
    try:
        index = session.get (url, headers = {'referer': url})

        index.raise_for_status()

        lpage = session.request (
                ** dogs.click (index.text, button, url, idx = 0), headers = {
                    'referer': url
                    })

                lpage.raise_for_status()

        propage = session.request (
                ** dogs.fill_form (
                    lpage.text, 
                    lpage.request.url , 
                    dogs.NO_TXTNODE_VALUE | dogs.NO_TXTNODE_KEY, 
                    data = ldata, 
                    idx = 0),
                headers = {
                    'referer': lpage.url,
                    'origin': url[0:-1],
                    'cache-control': 'max-age=0'
                    }
                )

        propage.raise_for_status()

        return propage

    except:
        return -1


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

        m = dogs.fill_form (res.text, res.url, flags =
                dogs.NO_TXTNODE_KEY | dogs.NO_TXTNODE_VALUE | dogs.DATAONLY,
                data = { 'ans': None })
        if 'qdescr' in m:
            return ( m, dogs.fill_form (res.text, res.url, flags = dogs.URLONLY)
                    )
        else:
            raise requests.HTTPError ('Not a Question Page', res)

#>>>>>>>>>>>>>>Body<<<<<<<<<<<<<<<<
    session = kwargs.pop ('session', requests)

    headers = kwargs.pop ('headers', None)

    if matno and crscode and html:
        req = requests.Request(
                ** dogs.fill_form( 
                    html, 
                    url = url, 
                    flags = dogs.NO_TXTNODE_KEY | dogs.NO_TXTNODE_VALUE, idx=0
                    ),
                headers = headers)
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


def convert_ans (row):
    a = r'\W+?'.join (row ['ans'].split ('+'))
    opts = row[3:]
    t = ('A', 'B', 'C', 'D')

    for i, tv in enumerate (t):
        if re.search (a, opts[i], flags = re.IGNORECASE):
            return tv
    return None

HACK = 0b01

def get_answer (db, qst, flag):

    conn = sqlite3.connect (db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor ()

    if flag & HACK:
        cur.execute ('''
                SELECT qdescr AS qdescr, ans AS ans, qid AS qid, opta AS opta,
                optb AS optb, optc AS optc, optd AS optd FROM questions
                AS q INNER JOIN (courses AS c, answers AS a, hacktab AS h) ON
                (c.dogid == q.dogid AND a.dogid == q.dogid AND a.cid == c.cid
                AND h.cid == c.cid)
                WHERE ready == 1 AND crscode LIKE ?
                ''', (
                    qst['crscode'],
                    ))
                row = cur.fetchone ()

        conn.close ()

        if not set (row.keys ()).issubset (set (qst.keys ())):
            return -1

        ans = {k: row[k] for k in row.keys ()}
        ans['ans'] = convert_ans(row)

        if not ans['ans']:
            return -1

        return ans


def setupdb (db):

    conn = sqlite3.connect (db)

    try:
        conn.executescript ('''
        CREATE TABLE IF NOT EXISTS questions (dogid INTEGER PRIMARY KEY
                AUTOINCREMENT, qdescr VARCHAR NOT NULL UNIQUE);

        CREATE TABLE IF NOT EXISTS courses (cid INTEGER PRIMARY KEY
                AUTOINCREMENT, crscode CHAR(6) DEFAULT NULL, dogid INTEGER NOT
                NULL REFERENCES questions (dogid) MATCH FULL ON DELETE CASCADE ON
                UPDATE CASCADE, ready BOOLEAN DEFAULT FALSE, qid CHAR);

        CREATE TABLE IF NOT EXISTS answers (ans VARCHAR DEFAULT NULL, dogid INTEGER
                NOT NULL REFERENCES questions (dogid) MATCH FULL ON DELETE
                CASCADE ON UPDATE CASCADE, cid INTEGER UNIQUE DEFAULT NULL
                REFERENCES courses (cid) MATCH FULL ON DELETE CASCADE ON
                UPDATE CASCADE);

        CREATE TABLE IF NOT EXISTS hacktab (cid INTEGER NOT NULL UNIQUE
        REFERENCES courses (cid), 
        opta VARCHAR NOT NULL,
        optb VARCHAR NOT NULL,
        optc VARCHAR NOT NULL,
        optd VARCHAR NOT NULL);
                ''')

        conn.commit ()
    except sqlite3.OperationalError as err:
        print ('create: ',err.args[0])
        conn.close ()
        return None

    return conn


def update_hacktab (db, data, cursor = None):

    conn = setupdb (db) if not cursor else cursor.connection

    conn.row_factory = sqlite3.Row

    if not conn:
        return -1

    cur = conn.cursor ()

    ierr = None

    dogid, cid, = None, None

    for datum in data:
        try:
            crsref = cur.execute ('''
                    SELECT * FROM courses WHERE qid = ? AND crscode = ?
                    ;''', (
                        datum['qid'], 
                        datum['crscode']
                        )).fetchone ()

                    if not crsref:
                        cid = updatedb (db, [datum], cur)['cid']

            else:
                cid = crsref['cid']

            cur.execute ('''
                    REPLACE INTO hacktab (cid, opta, optb, optc, optd) VALUES (?, ?,
                    ?, ?, ?);
                    ''', (
                        cid,
                        datum['opta'],
                        datum['optb'],
                        datum['optc'],
                        datum['optd']
                        ))
                    if cursor:
                        return cursor

        except sqlite3.OperationalError as err:
            print ('update_hacktab: replace: ', err.args[0])
            conn.close ()
            return -1

    try:
        conn.commit ()

    except sqlite3.OperationalError as err:
        print (err.args[0])
        return conn

    return None



def updatedb (db, data, cursor = None):

    repeats = 0

    conn = setupdb (db) if not cursor else cursor.connection

    conn.row_factory = sqlite3.Row

    if not conn:
        return -1

    cur = conn.cursor ()

    dogid, cid, = None, None

    ids = {}

    for datum in set (map ( 
        lambda t: QstDbT(
            re.sub (r'\\[ntr]', ' ', t['qdescr'].strip ()), 
            '+'.join (re.sub(r'\W', ' ',t['ans'].strip()).split ()) if isinstance (t['ans'], str) else t['ans'], 
            t['qid'].strip() if isinstance (t['qid'], str) else t['qid'],
            t['crscode'].strip().upper() if isinstance (t['crscode'], str) else t['crscode']
            ), 
        data)):

        try:
            cur.execute ('''INSERT INTO questions (qdescr)
                    VALUES (?);''', (datum.qdescr,))

            dogid = cur.lastrowid
            ids['dogid'] = dogid

            cur.execute ('''INSERT INTO courses (crscode, dogid, ready,
            qid) VALUES
                    (?, ?, ?, ?)''', (
                        datum.crscode,
                        dogid,
                        True if datum.ans and datum.crscode and datum.qid else
                        False,
                        datum.qid
                        ))

                    cid = cur.lastrowid            
            ids['cid'] = cid

            cur.execute ('''
                    INSERT INTO answers (ans, dogid, cid) VALUES (?, ?,
                    ?);
                    ''', (
                        datum.ans,
                        dogid,
                        cid
                        ))

                    if cursor:        
                        return ids

        except sqlite3.IntegrityError as ierr:

            repeats += 1

            dupq = cur.execute ('SELECT * FROM questions WHERE qdescr = ?', (datum.qdescr,)).fetchone ()

            crsref = cur.execute (''' 
                    SELECT * FROM courses WHERE (crscode = ? AND qid = ? AND
                    dogid = ?) OR (dogid = ? AND ready = ?) LIMIT 1
                    ''', (
                        datum.crscode,
                        datum.qid,
                        dupq['dogid'],
                        dupq['dogid'],
                        False
                        )).fetchone() or {
                                'cid': None, 
                                'dogid': dupq['dogid'],
                                'crscode': None,
                                'ready': False,
                                'qid': None
                                } 

                        ansref = cur.execute ('''SELECT * FROM answers WHERE (dogid =
                    ? AND cid = ?) OR dogid = ?;''', (
                        dupq['dogid'],
                        crsref['cid'],
                        dupq['dogid']
                        )).fetchone () or {
                                'ans': None, 
                                'dogid': None, 
                                'cid': None
                                }

                        cur1 = cur.connection.cursor ()

            cur1.execute (''' 
                    REPLACE INTO courses (cid, crscode, dogid, ready, qid)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (
                        crsref['cid'],
                        datum.crscode or crsref['crscode'],
                        crsref['dogid'],
                        True if (ansref['ans'] or datum.ans) and (datum.qid or
                            crsref['qid']) and (crsref['crscode'] or
                                datum.crscode) else False,
                            datum.qid or crsref['qid']
                            ))

                    cid = cur1.lastrowid

            ids['cid'] = cid

            ids['dogid'] = dupq['dogid']

            cur.execute (''' 
                    REPLACE INTO answers (ans, dogid, cid) VALUES (?,
                    ?, ?)
                    ''', (
                        datum.ans or ansref['ans'],
                        dupq['dogid'],
                        cid
                        ))

                    if cursor:
                        return ids

        except sqlite3.OperationalError as err:
            print ('insert/replace: ', err.args[0])
            conn.close ()
            return -1


    try:
        conn.commit ()

    except sqlite3.OperationalError as err:
        print (err.args[0])
        return conn

    if not cursor:
        conn.close()
    else:
        return cursor

    if repeats > 0:
        print ('%d questions repeated' % (repeats,))

    return None

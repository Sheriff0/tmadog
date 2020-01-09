import re
import dogs
import requests
import collections
import sqlite3
import hashlib
import builtins
import lxml

QstDbT = collections.namedtuple ('QstDbT', 'qdescr, ans, qid, crscode')

#CrsDbT = collections.namedtuple ('CrsDbT', 'crscode, qid, answered', defaults = [False])

def login (session, url, button = 'Login',**ldata):

    if not ldata:
        return -1

    try:
        index = session.get (url, headers = {'referer': url})

        index.raise_for_status()

        lpage = session.request ( ** dogs.click (index.text, button, url, idx = 0), headers = { 'referer': url })

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

def fetchtma (url, matno, tma , crscode, html, selector = 'form', idx = 0, **kwargs):

    def fetcher (url = None, headers = {}):
        url = url if url else req.url

        req.headers.update (**headers)

        res = session.post(url, data = dict (req.data), headers =
                req.headers)
        res.raise_for_status ()
        
        try:
            m = dogs.fill_form (res.text, res.url, data = { 'ans': None })

        except:
            raise requests.HTTPError ('Not a Question Page', res)

        return (m['data'], m['url'])

#>>>>>>>>>>>>>>Body<<<<<<<<<<<<<<<<
    session = kwargs.pop ('session', requests)

    headers = kwargs.pop ('headers', None)

    if matno and crscode and html:
        html = lxml.html.fromstring (html, base_url = url)
        data = {
                e.get ('name'): e.get ('value', '')
                for e in html.cssselect (selector)[idx].cssselect (':not(input)[name]')
                }
    
        args = dogs.fill_form( 
                    html, 
                    url = url,
                    selector = selector,
                    idx = idx
                    )

        data.update (**args['data'])

        args['data'], data = data, args['data']

        req = requests.Request( ** args , headers = headers)

        for k in req.data:
            req.data[k] = re.sub (r'nou\d{9}', matno.upper(), req.data[k], flags = re.IGNORECASE)

            req.data[k] = re.sub (r'[^nN1-9][^Oo1-9][^1-9Uu]\d{3}(?!\d+)',
                    crscode.upper(), req.data[k], flags = re.IGNORECASE)

            req.data[k] = re.sub (r'(tma)[1-3]', r'\g<1>' + str (tma), req.data[k], flags = re.IGNORECASE)


    else:
        raise requests.HTTPError ('Incomplete TMA details', requests.Response ())

    return fetcher


def convert_ans (
        row,
        a,
        pre = 'opt',
        optmap = {
            'opta': 'A',
            'optb': 'B',
            'optc': 'C',
            'optd': 'D'
            }
        ):
    a = re.sub (r'\+', r'\\W+?', a)

    for k in {k: row[k] for k in row if k.startswith (pre)}:

        if re.match (a, row [k].strip (), flags = re.IGNORECASE):
            return optmap[k] 

    return 'None'

HACK = 0b01
NORM = 0b10

def get_answer (
        db,
        qst,
        mode,
        ans = 'ans',
        qdescr = 'qdescr',
        qid = 'qid',
        crscode = 'crscode',
        optmap = {
            'opta': 'opta',
            'optb': 'optb',
            'optc': 'optc',
            'optd': 'optd'
            }
        ):
    
    def getter (qst, m):
        if not isinstance (qst, lxml.html.FieldsDict):
            raise TypeError ('question must be a form field')

        conn = sqlite3.connect (db)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor ()

        if m is NORM:
            row = {}
            cur.execute ('''
            SELECT ans AS %s FROM answers INNER JOIN courses AS
            c ON (c.crscode LIKE ? AND c.qid IS ? AND c.ready IS NOT FALSE) WHERE answers.cid IS c.cid
                    ''' % (
                        ans,
                        ), 
                    (
                        qst [crscode],
                        qst [qid]
                        )
                    )
            row [ans] = cur.fetchone ()[ans]

        elif m is HACK:
            cur.execute ('''
                SELECT qdescr AS %s, ans AS %s, qid AS %s, opta AS %s, optb AS
                %s, optc AS %s, optd AS %s FROM questions AS q INNER JOIN
                (courses AS c, answers AS a, hacktab AS h) ON (ready IS NOT
                        FALSE AND crscode LIKE ? AND a.cid == c.cid AND h.cid ==
                        c.cid) WHERE (c.dogid, a.dogid) IS (q.dogid, q.dogid)
                    ''' % (
                        qdescr,
                        ans,
                        qid,
                        optmap['opta'],
                        optmap['optb'],
                        optmap['optc'],
                        optmap['optd']
                        ), 
                    (
                        qst[crscode],
                        )
                    )
            
            row = cur.fetchone ()

            qst.update (
                    **{
                        k: row[k] for k in row if k is not ans
                        }
                    )

        conn.close ()

        qst[ans] = convert_ans(qst, row[ans])

        return qst

    def fetcher (qst, m = mode):
        a = None

        if len (lcache):
            a = lcache.get (qst[qid], None) if m is NORM else lcache.get
            (qst[crscode], None)
    
        if not a:
            a = getter (qst, m)
            lcache[qst[crscode]] = a.copy ()
            lcache[qst[qid]] = lcache[qst[crscode]]

        lcache = {}
        return fetcher


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

    for datum in set (data):

        try:

            if isinstance (datum, QstDbT):
                datum = datum._asdict ()
            cur.execute ('''INSERT INTO questions (qdescr)
                    VALUES (?);''', (datum['qdescr'],))

            dogid = cur.lastrowid
            ids['dogid'] = dogid

            cur.execute ('''INSERT INTO courses (crscode, dogid, ready,
            qid) VALUES
                    (?, ?, ?, ?)''', (
                        datum['crscode'],
                        dogid,
                        True if datum['ans'] and datum['crscode'] and datum['qid'] else
                        False,
                        datum['qid']
                        ))

            cid = cur.lastrowid            
            ids['cid'] = cid

            cur.execute ('''
                    INSERT INTO answers (ans, dogid, cid) VALUES (?, ?,
                    ?);
                    ''', (
                        datum['ans'],
                        dogid,
                        cid
                        ))

            if cursor:        
                return ids

        except sqlite3.IntegrityError as ierr:

            repeats += 1

            dupq = cur.execute ('SELECT * FROM questions WHERE qdescr = ?', (datum['qdescr'],)).fetchone ()

            crsref = cur.execute (''' 
                    SELECT * FROM courses WHERE (crscode = ? AND qid = ? AND
                    dogid = ?) OR (dogid = ? AND ready = ?) LIMIT 1
                    ''', (
                        datum['crscode'],
                        datum['qid'],
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
                        datum['crscode'] or crsref['crscode'],
                        crsref['dogid'],
                        True if (ansref['ans'] or datum['ans']) and (datum['qid'] or
                            crsref['qid']) and (crsref['crscode'] or
                                datum['crscode']) else False,
                            datum['qid'] or crsref['qid']
                            ))

            cid = cur1.lastrowid

            ids['cid'] = cid

            ids['dogid'] = dupq['dogid']

            cur.execute (''' 
                    REPLACE INTO answers (ans, dogid, cid) VALUES (?,
                    ?, ?)
                    ''', (
                        datum['ans'] or ansref['ans'],
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

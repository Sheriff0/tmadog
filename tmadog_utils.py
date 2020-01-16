import re
import dogs
import requests
import collections
import sqlite3
import hashlib
import builtins
import lxml
import random
from pathlib import PurePath
from urllib import parse

class TmadogUtils (object):
    QstDbT = collections.namedtuple ('QstDbT', 'qdescr, ans, qid, crscode')

    #CrsDbT = collections.namedtuple ('CrsDbT', 'crscode, qid, answered', defaults = [False])

    def login (html, url, session, buttons = [], **ldata):

        if not ldata:
            return -1

        try:
            url = parse.urlparse (url)

            for b in buttons:

                xpage = session.request (
                        ** dogs.click (
                            html,
                            button = b,
                            url = url.geturl (),
                            idx = 0
                            ), 
                        headers = { 'referer': url.geturl() }
                        )

                xpage.raise_for_status()
                html = xpage.text
                url = parse.urlparse (xpage.request.url)

            propage = session.request (
                    ** dogs.fill_form (
                        html,
                        url.geturl () ,
                        flags = dogs.NO_TXTNODE_VALUE | dogs.NO_TXTNODE_KEY,
                        data = ldata,
                        idx = 0
                        ),
                    headers = {
                        'referer': url.geturl (),
                        'origin': url.scheme + '://' + url.hostname,
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


    def fetchtma (url, matno, tma , crscode, html, button = 'TMA', idx = 0, **kwargs):

        def fetcher (url = None, headers = {}):
            url = url if url else req.url

            req.headers.update (**headers)

            res = session.post(url, data = dict (req.data), headers =
                    req.headers)
            res.raise_for_status ()

            try:
                m = dogs.fill_form (res.text, res.url, data = { 'ans': None })

            except:
                raise TypeError ('Not a Question Page', res)

            return (m['data'], m['url'])

    
        def copycase (repl):
            def _copycase(m):
                return repl.upper () if m['cs'].isupper () else repl.lower ()

            return _copycase


    #>>>>>>>>>>>>>>Body<<<<<<<<<<<<<<<<
        session = kwargs.pop ('session', requests)

        headers = kwargs.pop ('headers', None)

        if matno and crscode and html:

            args = dogs.click (
                        html,
                        url = url,
                        ltext = button,
                        idx = idx,
                        flags = dogs.EXTRAS
                        )


            args['url'] = re.sub (r'(?P<cs>nou)\d{9}', copycase (matno), args['url'], flags = re.IGNORECASE)

            args['url'] = re.sub (r'(?P<cs>[^nN1-9][^Oo1-9][^1-9Uu])\d{3}(?!\d+)',
                    copycase (crscode), args['url'], flags = re.IGNORECASE)

            args['url'] = re.sub (r'(?P<cs>tma)[1-3]', copycase(r'tma' + str
                (tma)), args['url'], flags = re.IGNORECASE)

            t = 'data' if args['method'] in ('POST', 'post') else 'params'

            for k in args.get(t, {}):
                args[t][k] = re.sub (r'(?P<cs>nou)\d{9}', copycase (matno), args[t][k], flags = re.IGNORECASE)

                args[t][k] = re.sub (r'(?P<cs>[^nN1-9][^Oo1-9][^1-9Uu])\d{3}(?!\d+)',
                        copycase (crscode), args[t][k], flags = re.IGNORECASE)

                args[t][k] = re.sub (r'(?P<cs>tma)[1-3]', copycase(r'tma' + str
                    (tma)), args[t][k], flags = re.IGNORECASE)


            req = requests.Request( ** args , headers = headers)

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
                SELECT ans AS %s FROM answers INNER JOIN (courses AS c,
                questions as q) ON ((c.crscode LIKE ? AND c.qid IS ? AND c.ready
                IS NOT FALSE) OR q.qdescr LIKE ?) WHERE answers.cid IS c.cid OR
                answers.dogid IS q.dogid
                        ''' % (
                            ans,
                            ),
                        (
                            qst [crscode],
                            qst [qid],
                            qst [qdescr],
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


    #__all__ = ['submit', 'hack', 'scrape_tmaQ']

    class QMiter (object):

        def __init__ (self, miter):
            self.miter = miter

        def __iter__ (self):

            for m in self.miter:
                if not re.fullmatch (r'\s+',m['qdescr']) and not re.fullmatch (r'\s+', m['ans']):
                    yield QstDbT (m['qdescr'].strip (), m['ans'].strip (),
                            m['qid'].strip (), m['crscode'].strip ())

        def __next__ (self):

            for m in self.miter:
                if not re.fullmatch (r'\s+',m['qdescr']) and not re.fullmatch (r'\s+', m['ans']):
                    return QstDbT (m['qdescr'].strip (), m['ans'].strip (),
                            m['qid'].strip (), m['crscode'].strip ())


    TMADOGDB = 'tmadogdb'

    def scraper_submitter_net (
            url,
            session,
            stp = 10,
            mode = NORM,
            **kwargs
            ):

        dt = []

        try:
            fetch = fetchtma (url, session = session, **kwargs)

            qst, url = fetch()
            dt.append (qst.copy())
            getans = get_answer (TMADOGDB, qst, mode)
            qn = int ('0' + qst['qj']) # Just in case it's empty

            while 1 <= qn <= stp:
                kont = session.post (url, data = dict (getans (qst)), headers = {
                    'referer': url,
                    })
                kont.raise_for_status ()

                qst, url = fetch()

                qn = int ('0' + qst['qj'])

                dt.append (qst.copy ())

        except builtins.BaseException as err:
            print (err.args[0])

        finally:
            if len (dt):
                return dt
            else:
                return -1


    def scraper_net (nqst, **kwargs):

        dt = []
        try:
            fetch = fetchtma (rl, **kwargs)
            while nqst:
                m = fetch()[0]
                dt.append (m)
                nqst -= 1

        except BaseException as err:
            print (err.args[0])

        finally:
            if len (dt):
                return dt
            else:
                return -1




    def prowl_tma (url, session, stp = 10, db = TMADOGDB, **kwargs): # TODO

        # NOTE: send with qj = qj + 1
        dt = []

        try:
            fetch = fetchtma (url, session = session, **kwargs)

            qst, url = fetch()
            qn = 1
            cur = setupdb (db).cursor ()
            ready = False

            while 1 <= qn <= stp:
                prevscr = int ('0' + qst['totscore'])
                ready = cur.execute ('''
                        SELECT ready from courses WHERE crscode = ? AND qid = ?
                        ''', (
                            qst['crscode'],
                            qst['qid']
                            )).fetchone ()[0]
                # FIXME: This will suffer if NOUN stops selecting questions
                # randomly

                opts = ['A', 'B', 'C', 'D']
                while not ready and prevscr < int ('0' + qst['totscore']) and len (opts):
                    opt = random.choice (opts)
                    opts.remove (opt)
                    qst['ans'] = opt
                    kont = session.post (url2, data = dict (qst), headers = {
                    'referer': url,
                    })
                    kont.raise_for_status ()

                else:
                    if not len (opts) and prevscr < int (qst['qj']):
                        print ('NOTE: %s: has no answer' % (qst['qdescr'],))

        except:
            pass


    def scraper_regex_f_or_str (
            f_or_str,
            regex = r'qtn\s*:.*?\n(?P<qdescr>.+?)^\W*ans\s*:.*?\n(?P<ans>.+?)(?P<qid>)(?P<crscode>)\n',
            enc = 'utf-8',
            flags = re.MULTILINE | re.IGNORECASE | re.DOTALL):

        if isinstance (f_or_str, PurePath):
            try:
                f = open (str (f_or_str), 'rt', encoding = enc)

                f_or_str = f.read ()

            except UnicodeDecodeError:
                f.reconfigure (encoding = 'utf-16le')
                f.seek (0)

                f_or_str = f.read ()

            except :
                return -1

            f.close ()

        return QMiter (re.finditer (regex, f_or_str, flags = flags ))


    def scraper_html_f_or_str (f_or_str, url = 'https://foo/foo.ext' , ans = None):
        try:
            if isinstance (f_or_str, PurePath):
                f_or_str = lxml.html.parse (str (f_or_str), base_url = url).getroot ()

            return [
                    dogs.fill_form (
                        f_or_str,
                        url = url,
                        flags = dogs.NO_TXTNODE_KEY | dogs.NO_TXTNODE_VALUE | dogs.DATAONLY,
                        data = { 'ans': ans }
                        )
                    ]
        except:
            return -1


    def scrapetma (
            scraper,
            updater,
            db = TMADOGDB,
            *ukwargs,
            **skwargs
            ):

        return updater (db, scraper (**skwargs), *ukwargs)


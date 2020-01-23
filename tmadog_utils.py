import re
import dogs
import requests
import collections
import sqlite3
import hashlib
import builtins
import lxml
import random
import parse as _parse
from pathlib import PurePath
from urllib import parse
import configparser

ANS_MODE_HACK = 0b01
ANS_MODE_NORM = 0b10

class TmadogUtils (object):
    
    QstDbT = collections.namedtuple ('QstDbT', 'qdescr, ans, qid, crscode')

    #CrsDbT = collections.namedtuple ('CrsDbT', 'crscode, qid, answered', defaults = [False])

    def login (
            html,
            url,
            session,
            **ldata
            ):

        if not ldata:
            return -1

        try:
            url = parse.urlparse (url)

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


    def nav_to (html, url, buttons, session):

        for b in buttons:

            xpage = session.request (
                    ** dogs.click (
                        html,
                        button = b,
                        url = url,
                        idx = 0
                        ),
                    headers = {
                        'referer': url,
                        'host': parse.urlparse (url).hostname
                        }
                    )

            xpage.raise_for_status()

            url = xpage.request.url
            html = xpage.text

        return xpage


    class AnsMgr (object):

        def __init__ (
                self,
                qmap,
                database,
                opt_names,
                pseudo_ans = [
                    'A',
                    'B',
                    'C',
                    'D'
                    ],
                mode = ANS_MODE_NORM,
                interactive = True,
                ):

            self.opt_map = {
                    a: b for a, b in zip (['a', 'b', 'c', 'd'], opt_names.sort ())
                    }

            self.pseudos = pseudo_ans.sort ()
            self.interactive = interactive
            self.mode = mode
            self.database = database
            self._cache = {}
            self._cur = None
            self.qdescr = qmap['qdescr']
            self.ans = qmap['ans']
            self.prefix = qmap['prefix']
            self.crscode = qmap['crscode']
            self.qid = qmap['qid']
            self.qn = qmap ['qn']
            self.score = qmap ['score']

        class CacheIter (object):
            def __init__ (self, cache):
                self.cache = cache

            def __iter__ (self):

                for k in self.cache:
                    if k.isupper ():
                        for k1 in self.cache [k]:
                            yield self.cache[k][k1]

            def __next__ (self):

                for k in self.cache:
                    if k.isupper ():
                        for k1 in self.cache [k]:
                            return self.cache[k][k1]



        hints = [
                (
                    '''Submit: The answer to this question is not in the database, can you answer it ?''',
                    '''Type '%s' if answer corresponds to row %s or type ':hack' to switch to hack mode.'''
                    ),

                (
                    '''Hack: I currently can't hack questions for this course, can you answer this question please ?''',
                    '''Type '%s' if answer corresponds to row %s and so on.'''
                    ),

                (
                    '''Fail: I failed the answer to this question. Please can you answer it ?''',
                    )
        ]

        def _copycase (self, t, i):
            return i.upper () if t.isupper () else i.lower ()
        
        def _qpromt (self, qst, epilog = None, prolog = None):

            x = input ('''%s
            %s. %s

            %s. %s 
            %s. %s 
            %s. %s 
            %s. %s 

%s
                    (type ':quit' to quit and leave question unanswered) --> ''' % (
                        prolog or '(tmadog)',
                        qst [self.qn],
                        qst [self.qdescr],
                        self.pseudos [0],
                        qst [self.opt_map ['a']],
                        self.pseudos [1],
                        qst [self.opt_map ['b']],
                        self.pseudos [2],
                        qst [self.opt_map ['c']],
                        self.pseudos [3],
                        qst [self.opt_map ['d']],
                        epilog or '''Type '%s' if answer corresponds to row %s and so on.''' % (pseudos[0], pseudos[0])
,
                        )
                    )

            return x


        def qprompt (self, qst, epilog = None, prolog = None, max_retry = 0,
                err_msg = None):

            x = self._qpromt (qst, epilog, prolog)
            try:
                qst [self.ans] = self._copycase (pseudos[0], x) if len (x) and not x.startswith (':') else None

            except ValueError:

                while max_retry:
                    x = self._qpromt (
                            qst,
                            epilog,
                            (err_msg or '''Error: You have entered an invalid option. %d attempt(s) left''') % ( max_retry, )
                            )
                    try:
                        qst [self.ans] = self._copycase (pseudos[0], x) if len (x) and not x.startswith (':') else None
                        break

                    except ValueError:
                        pass

                    max_retry -= 1


            finally:
                self.update (qst.copy ())
                return x

        def check (self, qst, mark):
            if mark is 0:
                if not self.interactive:
                    qst[self.ans] = None
                    self.update (qst.copy ())
                else:
                    msg = self.hints [-1]
                    self.qprompt (qst, prolog = msg[0], max_retry = 3)

        def answer (self, qst):

            if not isinstance (qst, lxml.html.FieldsDict):
                raise TypeError ('Question must be a form', type (qst))

            if self.mode is ANS_MODE_NORM:
                x = self._cache.get ( qst [self.crscode].upper (), None)

                if x:
                    x = x.get (self.qid, None)
                    if x and x[self.ans]:
                        return x
                    else:
                        x = None

                if not x:

                    x = self._fetch (qst)
                    if x:
                        x = self.convert_ans (qst, x[self.ans])
                        if x:
                            qst [self.ans] = x
                            self.update (qst.copy ())
                            return qst

                        else:
                            return self.resolve (qst)


            if self.mode is ANS_MODE_HACK:
                x = self._cache.get (qst [self.crscode].lower (), None) or self._hack (qst)

                if x and x.get (qst [self.crscode], None):
                    return x

                elif x and x.get (self.ans, None):
                    x[self.ans] = self.convert_ans (
                            {
                                k: x[k] for k in x if k.startswith (self.prefix)
                                },
                            x[self.ans]
                            )

                    if x[self.ans]:
                        qst.update (x)
                        self.update (qst.copy ())
                        return qst

                if not x or not x.get (self.ans, None):
                    return self.resolve (qst)

        def update (self, qst):

            self._cache.setdefault (qst [self.crscode].upper (), {})

            self._cache[qst [self.crscode].upper ()].setdefault (qst [self.qid],
                    qst)

            if qst [self.ans]:
                self._cache.setdefault (qst [self.crscode].lower (), qst)

            else:
                x = self._cache.get (qst [self.crscode].lower (), None)
                if x and x [self.qid] is qst [self.qid]:
                    self._cache.pop (qst [self.crscode].lower ())

        def resolve (self, qst):

            if not self.interactive:
                return None

            msg = self.hints [self.mode]
            x = self.qprompt (
                    qst,
                    prolog = msg[0],
                    epilog = msg[1] % (pseudos[0], pseudos[0]),
                    max_retry = 3
                    )

            if x in (':hack', ':Hack', ':HACK'):
                self.mode = ANS_MODE_HACK
            return None if not qst[self.ans] else qst
            


        def convert_ans (self, qst, ans):
            ans = re.sub (r'\+', r'\\W+?', ans)

            for a, p in zip (self.opt_map.values ().sort (), self.pseudos):

                if re.match (ans, qst[a].strip (), flags = re.IGNORECASE):
                    return p

            return None


        def iter_cache (self):

            return CacheIter (self._cache)

        def close (self):

            self._cur.connection.close ()

        def _hack (self, qst):

            if not self._cur:
                conn = sqlite3.connect (self.database)
                conn.row_factory = sqlite3.Row
                self._cur = conn.cursor ()

            self._cur.execute ('''
                SELECT qdescr AS %s, ans AS %s, qid AS %s, opta AS %s, optb AS
                %s, optc AS %s, optd AS %s FROM questions AS q INNER JOIN
                (courses AS c, answers AS a, hacktab AS h) ON (ready IS NOT
                        FALSE AND crscode LIKE ? AND a.cid == c.cid AND h.cid ==
                        c.cid) WHERE (c.dogid, a.dogid) IS (q.dogid, q.dogid)
                    ''' % (
                        self.qdescr,
                        self.ans,
                        self.qid,
                        self.opt_map['a'],
                        self.opt_map['b'],
                        self.opt_map['c'],
                        self.opt_map['d']
                        ),
                    (
                        qst[self.crscode],
                        )
                    )

            return self._cur.fetchone ()

        def _fetch (self, qst):

            if not self._cur:
                conn = sqlite3.connect (self.database)
                conn.row_factory = sqlite3.Row
                self._cur = conn.cursor ()

            self._cur.execute ('''
            SELECT ans AS %s FROM answers INNER JOIN (courses AS c,
            questions as q) ON ((c.crscode LIKE ? AND c.qid IS ? AND c.ready
            IS NOT FALSE) OR q.qdescr LIKE ?) WHERE answers.cid IS c.cid OR
            answers.dogid IS q.dogid
                    ''' % (
                        self.ans,
                        ),
                    (
                        qst [self.crscode],
                        qst [self.qid],
                        qst [self.qdescr],
                        )
                    )

            return self._cur.fetchone ()



    class QstMgr (object):

        def __init__ (self, html, url, matno, tma , crscode, qmap, fb, stop = 10, button = 'TMA', idx
                = 0, session = requests):

            self.session = session

            self.referer = url

            self.referer1 = None

            self.score = 0

            self.data = None

            self.qn = qmap['qn']

            self.ans = qmap ['ans']

            self.nextq = None

            self.stop = stop

            self.count = 0

            self.fargs = dogs.click (
                        html,
                        url = url,
                        button = button,
                        idx = idx,
                        flags = dogs.FILL_FLG_EXTRAS
                        )

            self.fargs = self._transform_req (self.fargs, matno, tma, crscode)

        def _transform_req (self, req, matno, tma , crscode):
            
            req['url'] = re.sub (r'(?P<cs>nou)\d{9}', self._copycase (matno), req['url'], flags = re.IGNORECASE)

            req['url'] = re.sub (r'(?P<cs>[^nN1-9][^Oo1-9][^1-9Uu])\d{3}(?!\d+)',
                    self._copycase (crscode), req['url'], flags = re.IGNORECASE)

            req['url'] = re.sub (r'(?P<cs>tma)[1-3]', self._copycase(r'tma' + str
                (tma)), req['url'], flags = re.IGNORECASE)
            
            self.data = 'data' if req['method'] in ('POST', 'post') else 'params'

            for k in req.get(self.data, {}):
                req[self.data][k] = re.sub (r'(?P<cs>nou)\d{9}', self._copycase (matno), req[self.data][k], flags = re.IGNORECASE)

                req[self.data][k] = re.sub (r'(?P<cs>[^nN1-9][^Oo1-9][^1-9Uu])\d{3}(?!\d+)',
                        self._copycase (crscode), req[self.data][k], flags = re.IGNORECASE)

                req[self.data][k] = re.sub (r'(?P<cs>tma)[1-3]', self._copycase(r'tma' + str
                    (tma)), req[self.data][k], flags = re.IGNORECASE)

                return req


        def fetch (self, url1 = None, **kwargs):
            if self.count is self.stop:
                return False

            self.fargs.update (url = url1 or self.fargs['url'])
            
            x = parse.urlparse (self.fargs ['url'])

            kwargs.setdefault (
                    'headers',
                    {
                        'referer': self.referer,
                        'host': '%s://%s' % (x.scheme, x.hostname),
                        }
                    )

            res = self.session.request(**self.fargs , **kwargs)

            res.raise_for_status ()

            self.referer1 = res.url
            
            x = dogs.fill_form (
                    res.text,
                    res.url,
                    flags = FILL_FLG_EXTRAS,
                    data = {
                        self.ans: None
                        }
                    )

            self.count = int (x [self.data][self.qn])
            self.nextq = x

            return True
            

        def _copycase (self, repl):
            def __copycase(m):
                return repl.upper () if m['cs'].isupper () else repl.lower ()

            return __copycase


        def reconfigure (self, matno, tma , crscode):


            self.fargs = self._transform_req (self.fargs, matno, tma, crscode)
            return self

        def submit (self, req, **kwargs):
            x = parse.urlparse (req ['url'])
            kwargs.setdefault (
                    'headers',
                    {
                        'referer': self.referer1,
                        'host': '%s://%s' % (x.scheme, x.hostname),

                        }
                    )

            res = self.session.request (**req, **kwargs)

            res.raise_for_status ()

            self.referer = res.url

            res = _parse.search (self.fb, res.text)['result']

            self.score = int (res['score'])
            return int (res['mark'])
            


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

    def submitter (
            ans_mgr: AnsMgr,
            qst_mgr: QstMgr
            ):

        try:

            while qst_mgr.fetch():
                
                preq = qst_mgr.nextq

                qst = preq[qst_mgr.data]

                preq[qst_mgr.data] = ans_mgr.answer (qst)

                if preq[qst_mgr.data]:
                    ans_mgr.check (
                            preq[qst_mgr.data],
                            qst_mgr.submit (preq)
                        )

                elif preq[qst_mgr.data] is False:
                    return False

                elif preq[qst_mgr.data] is None:
                    pass

        except builtins.BaseException as err:
            print (err.args[0])

            return -1


    def scraper_net (nqst, fetcher, ans = 'ans'):

        dt = []
        try:
            purl = parse.urlparse (fetcher.referer)

            while nqst:
                m = dogs.fill_form (
                        *fetcher.fetch(
                            headers = {
                                'referer': purl.geturl (),
                                'host': '%s://%s' % (purl.scheme, purl.hostname)
                                }
                            ),
                        flags = dogs.FILL_RET_DATAONLY,
                        data = {
                            ans: None,
                            }
                        )
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
            fetch = QstMgr (url, session = session, **kwargs)

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
                        flags = dogs.NO_TXTNODE_KEY | dogs.NO_TXTNODE_VALUE | dogs.FILL_RET_DATAONLY,
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

        return updater (db, *ukwargs, data = scraper (**skwargs))


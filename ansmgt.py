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

class AnsMgt (object):

    class AnsMgr (object):

        def __init__ (
                self,
                qmap,
                database,
                mode,
                pseudo_ans = [
                    'A',
                    'B',
                    'C',
                    'D'
                    ],
                interactive = True,
                ):


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
                yield from self.__next__ ()

            def __next__ (self):

                for k in self.cache:
                    if k.isupper ():
                        for k1 in self.cache [k]:
                            yield self.cache[k][k1]



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
                        qst [self.qmap ['a']],
                        self.pseudos [1],
                        qst [self.qmap ['b']],
                        self.pseudos [2],
                        qst [self.qmap ['c']],
                        self.pseudos [3],
                        qst [self.qmap ['d']],
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

            self._cache[qst [self.crscode].upper ()].update ([(qst [self.qid],
                    qst)])

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
            x = [self.qmap [k] for k in ['a', 'b', 'c', 'd']]

            for a, p in zip (x, self.pseudos):

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
                        self.qmap['a'],
                        self.qmap['b'],
                        self.qmap['c'],
                        self.qmap['d']
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

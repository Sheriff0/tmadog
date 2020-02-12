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
ANS_MODE_NORM = 0b00

class AnsMgt:

    ANS_MODE_HACK = 0b01
    ANS_MODE_NORM = 0b00

    class AnsMgr (object):

        def __init__ (
                self,
                qmap,
                database,
                mode,
                pseudo_ans,
                interactive = True,
                max_retry = 3,
                ):


            self.pseudos = pseudo_ans
            self.interactive = interactive
            self.mode = mode
            self.database = database
            self._cache = {}
            self._cur = None
            self.qmap = qmap
            self.max_retry = max_retry

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
                    '''Norm: The answer to this question is not in the database, can you answer it ?''',
                    '''Type '%s' if answer corresponds to row %s or type ':hack' to switch to hack mode.'''
                    ),

                (
                    '''Hack: I currently can't hack questions for this course, can you answer this question please ?''',
                    '''Type '%s' if answer corresponds to row %s and so on.'''
                    ),

                (
                    '''Fail: I failed the answer to this question. Please can you answer it ?''',
                    '''Type '%s' if answer corresponds to row %s and so on.'''
                    )
        ]

        def __call__ (self, qstlike, d = None):
            return self._cache [qstlike [self.qmap ['crscode']].upper ()][qstlike [self.qmap ['qid']]][d] if d else self._cache [qstlike [self.qmap ['crscode']].upper ()][qstlike [self.qmap ['qid']]] # UGLY
        
        def _copycase (self, t, i):
            return i.upper () if t.isupper () else i.lower ()
        
        def _mkprompt (self):
            txt = '''{prolog}

{%s}. {%s}

''' % (self.qmap ['qn'], self.qmap ['qdescr'])

            for i in range (len (self.pseudos)):
                k = 'opt' + bytes ([65+i]).decode ()
                txt += '%s: {%s}\n' % (self.pseudos [i], self.qmap [k])

            txt += '''
            {epilog}
            (type ':quit' to quit and leave question unanswered) --> '''

            return txt

        def _qpromt (self, qst, epilog = None, prolog = None):
            
            if not hasattr (self, 'p_text'): 
                self.p_text = self._mkprompt ()

            x = input (self.p_text.format (
                prolog = prolog or '(tmadog)',
                epilog = epilog or '''Type '%s' if answer corresponds to row %s and so on.''' % (self.pseudos[0], self.pseudos[0]), 
                **qst
                )
                )

            return x


        def qprompt (self, qst, epilog = None, prolog = None, max_retry = 0,
                err_msg = None):

            x = self._qpromt (qst, epilog, prolog)
            try:
                qst [self.qmap ['ans']] = self._copycase (self.pseudos[0], x) if len (x) and not x.startswith (':') else None

            except ValueError:

                while max_retry:
                    x = self._qpromt (
                            qst,
                            epilog,
                            (err_msg or '''
Error: You have entered an invalid option. %d attempt(s) left''') % ( max_retry, )
                            )
                    try:
                        qst [self.qmap ['ans']] = self._copycase (self.pseudos[0], x) if len (x) and not x.startswith (':') else None
                        break

                    except ValueError:
                        pass

                    max_retry -= 1


            finally:

                return x

        def check (self, qst, mark):
            if mark is 0:
                qst = qst.copy ()

                if not self.interactive:
                    qst[self.qmap ['ans']] = None
                else:
                    msg = self.hints [-1]
                    x = self.qprompt (qst, prolog = msg[0], max_retry = self.max_retry)
                    if x in (':hack', ':Hack', ':HACK'):
                        self.mode = ANS_MODE_HACK
                
                return self.update (qst.copy ())

        def answer (self, qst):

            if not isinstance (qst, lxml.html.FieldsDict):
                raise TypeError ('Question must be a form', type (qst))

            if self.mode is ANS_MODE_NORM:
                x = self._cache.get ( qst [self.qmap ['crscode']].upper (), None)

                if x:
                    x = x.get (self.qmap ['qid'], None)
                    if x and x[self.qmap ['ans']]:
                        return x
                    else:
                        x = None

                if not x:

                    x = self._fetch (qst)
                    if x and x [self.qmap ['ans']]:
                        x = self.convert_ans (qst, x[self.qmap ['ans']])
                        if x:
                            qst [self.qmap ['ans']] = x
                            self.update (qst.copy ())
                            return qst

                        else:
                            return self.resolve (qst)

                    else:
                        return self.resolve (qst)


            if self.mode is ANS_MODE_HACK:
                x = self._cache.get (qst [self.qmap ['crscode']].lower (), None) or self._hack (qst)

                if x and self.qmap ['crscode'] in x:
                    qst.update (x)
                    return qst

                elif x and x[self.qmap ['ans']]:
                    x = dict (x)
                    x [self.qmap ['ans']] = self.convert_ans (x, x[self.qmap ['ans']])

                    if x [self.qmap ['ans']]:
                        qst.update (x)
                        self.update (qst.copy ())
                        return qst
                    else:
                        return self.resolve (qst)

                else:
                    return self.resolve (qst)

        def update (self, qst):
            
            i = 0
            while True:
                try:
                    qst.pop (self.qmap ['id' + str (i)])
                    i += 1
                except KeyError:
                    break

            self._cache.setdefault (qst [self.qmap ['crscode']].upper (), {})

            self._cache[qst [self.qmap ['crscode']].upper ()].update ([(qst
                [self.qmap ['qid']],
                    qst)])

            if qst [self.qmap ['ans']]:
                self._cache.setdefault (qst [self.qmap ['crscode']].lower (), qst)

            else:
                x = self._cache.get (qst [self.qmap ['crscode']].lower (), None)
                if x and x [self.qmap ['qid']] is qst [self.qmap ['qid']]:
                    self._cache.pop (qst [self.qmap ['crscode']].lower ())

        def resolve (self, qst):

            if not self.interactive:
                return None

            msg = self.hints [self.mode]
            x = self.qprompt (
                    qst,
                    prolog = msg[0],
                    epilog = msg[1] % (self.pseudos[0], self.pseudos[0]),
                    max_retry = self.max_retry
                    )

            if x in (':hack', ':Hack', ':HACK'):
                self.mode = ANS_MODE_HACK
            self.update (qst.copy ())

            return None if not qst[self.qmap ['ans']] else qst
            


        def convert_ans (self, qst, ans):
            ans = re.sub (r'\+', r'\\W+?', ans)

            for i in range (len (self.pseudos)):
                k = 'opt' + bytes ([97+i]).decode ()
                if re.match (ans, qst[self.qmap [k]].strip (), flags = re.IGNORECASE):
                    return self.pseudos [i]

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
                        self.qmap ['qdescr'],
                        self.qmap ['ans'],
                        self.qmap ['qid'],
                        self.qmap['opta'],
                        self.qmap['optb'],
                        self.qmap['optc'],
                        self.qmap['optd']
                        ),
                    (
                        qst[self.qmap ['crscode']],
                        )
                    )

            return self._cur.fetchone ()

        def _fetch (self, qst):

            if not self._cur:
                conn = sqlite3.connect (self.database)
                conn.row_factory = sqlite3.Row
                self._cur = conn.cursor ()

            self._cur.execute ('''
            SELECT ans AS %s FROM answers INNER JOIN (courses) ON (courses.crscode LIKE ? AND courses.qid IS ? AND courses.ready
            IS NOT FALSE) WHERE answers.cid IS courses.cid
                    ''' % (
                        self.qmap ['ans'],
                        ),
                    (
                        qst [self.qmap ['crscode']],
                        qst [self.qmap ['qid']],
                        )
                    )

            r = self._cur.fetchone ()

            if not r:

                self._cur.execute ('''
                SELECT ans AS %s FROM answers INNER JOIN questions ON qdescr LIKE ? WHERE answers.dogid IS questions.dogid
                        ''' % (
                            self.qmap ['ans'],
                            ),

                        (
                            qst [self.qmap ['qdescr']],
                            )
                        )

                r = self._cur.fetchone ()

            return r

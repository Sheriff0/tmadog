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
import sys
import curses


class QstMgt (object):

    class QstMgr (object):

        class StrCList (list):
            def __init__ (self, iter):

                for x in iter:
                    self.append (x)

            def append (self, value):
                
                v = str (value).lower ()
                try:
                    i = self.index (v)
                    self [i+1] += 1

                except ValueError:
                    super ().extend ([v, 1])

                return
            
            def extend (self, iter):
                return self.__init__ (iter)


        def __init__ (self, fargs, url, matno, tma , crscode, qmap,
                stop = 10, session = requests):

            self.session = session

            self.referer = url

            self.referer1 = None

            self.dt0 = None

            self.dt1 = None

            self.qmap = qmap

            self.pseudos = self.qmap ['pseudo_ans'].split (',')

            self.totscore = 0

            self.nextq = {}

            self.stop = stop

            self.count = True

            self.interactive = False

            self.fargs = self._transform_req (fargs, matno, tma, crscode)

        def _transform_req (self, req, matno, tma , crscode):
            
            self.dt0 = 'data' if req['method'] in ('POST', 'post') else 'params'
            req['url'] = re.sub (r'(?P<cs>nou)\d{9}', self._copycase (matno), req['url'], flags = re.IGNORECASE)

            req['url'] = re.sub (r'(?P<cs>[A-Za-z]{3})\d{3}(?!\d+)',
                    self._copycase (crscode), req['url'], flags = re.IGNORECASE)

            req['url'] = re.sub (r'(?P<cs>tma)[1-3]', self._copycase(r'tma' + str
                (tma)), req['url'], flags = re.IGNORECASE)
            

            for k in req.get(self.dt0, {}):
                req[self.dt0][k] = re.sub (r'(?P<cs>nou)\d{9}', self._copycase (matno), req[self.dt0][k], flags = re.IGNORECASE)

                req[self.dt0][k] = re.sub (r'(?P<cs>[A-Za-z]{3})\d{3}(?!\d+)',
                        self._copycase (crscode), req[self.dt0][k], flags = re.IGNORECASE)

                req[self.dt0][k] = re.sub (r'(?P<cs>tma)[1-3]', self._copycase(r'tma' + str
                    (tma)), req[self.dt0][k], flags = re.IGNORECASE)

            return req


        def fetch (self, url1 = None, **kwargs):
            if not self.stop:
                return self.nextq.pop (self.dt1 or self.dt0, None)

            if (self.dt1 or self.dt0) not in self.nextq:
                self.fargs.update (url = url1 or self.fargs['url'])
                
                kwargs.setdefault (
                        'headers',
                        dogs.mkheader (self.fargs ['url'], self.referer)
                        )

                try:
                    self.qres = self.session.request(**self.fargs , **kwargs)

                    self.qres.raise_for_status ()
                    self.referer1 = self.qres.url
                    self.nextq = dogs.fill_form (
                            self.qres.text,
                            self.qres.url,
                            flags = dogs.FILL_FLG_EXTRAS,
                            data = {
                                self.qmap ['ans']: None
                                }
                            )

                    self.count = int ('' + self.nextq [self.dt1 or self.dt0][self.qmap ['qn']])
                    
                    if self.count == self.stop:
                        self.stop = False

                except TypeError:

                    if self.interactive:
                        return self.geterrmsg (self.qres)
                    else:
                        raise TypeError ('Invalid question page', self.qres)

                except BaseException as err:
                    if self.interactive:
                        return self.geterrmsg (err)
                    else:
                        raise TypeError ('Invalid question page', self.qres)
           
            
            if not self.dt1:
                self.dt1 = 'data' if self.nextq ['method'] in ('POST', 'post') else 'params'

            return self.nextq.pop (self.dt1)

        def _copycase (self, repl):
            def __copycase(m):
                return repl.upper () if m['cs'].isupper () else repl.lower ()

            return __copycase


        def reconfigure (self, matno, tma , crscode, stop = 10):


            self.totscore = 0

            self.nextq = None

            self.stop = stop

            self.count = 0

            self.fargs = self._transform_req (self.fargs, matno, tma, crscode)
            return self

        def submit (self, qst, **kwargs):

            if qst [self.qmap ['qid']] == 'error':
                if qst [self.qmap ['ans']] == '1':
                    self.stop = True
                    self.pseudos = self.bkpseudo
                else:
                    self.stop = False

                return None


            self.nextq [self.dt1 or self.dt0] = qst
            
            self.totscore = int ('0' + qst [self.qmap ['score']])

            kwargs.setdefault (
                    'headers',
                    dogs.mkheader (self.nextq ['url'], self.referer1)
                    )

            res = self.session.request (**self.nextq, **kwargs)

            res.raise_for_status ()

            x = self.nextq.pop (self.dt1 or self.dt0)

            y = res

            self.referer = res.url

            res = self.fetch ()

            if not res:
                if self.interactive:
                    qst = self.geterrmsg (y)
                    self.nextq [self.dt1] = qst
                    return None


            self.nextq [self.dt1 or self.dt0] = res
            
            if not res [self.qmap ['qid']] == 'error':
                s = (int ('0' + res[self.qmap ['score']]) - self.totscore) == 1

                self.totscore = int ('0' + res[self.qmap ['score']])

                return int (s)
            
        def geterrmsg (self, res):

            if isinstance (res, Exception):
                res = repr (res)
            else:
                res = lxml.html.fromstring (res.text).text_content ()

            self.bkpseudo = self.pseudos
            self.pseudos = [ curses.A_INVIS | ord (o) for o in ('1', '0') ] if sys.stdout.isatty () else ('1', '0')

            return {
                    self.qmap ['qdescr']: res,
                    self.qmap ['ans']: None,
                    self.qmap ['opta']: 'retry',
                    self.qmap ['optb']: 'exit',
                    self.qmap ['qid']: 'error',
                    self.qmap ['qn']: 'X',
                    }





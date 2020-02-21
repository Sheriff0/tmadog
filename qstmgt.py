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

            self.score = qmap['score']

            self.qn = qmap['qn']

            self.ans = qmap ['ans']

            self.totscore = 0

            self.nextq = {}

            self.stop = stop

            self.count = True

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
                return self.nextq.pop (self.dt1, None)

            if (self.dt1 or self.dt0) not in self.nextq:
                self.fargs.update (url = url1 or self.fargs['url'])
                
                x = parse.urlparse (self.fargs ['url'])

                kwargs.setdefault (
                        'headers',
                        {
                            'referer': self.referer,
                            'host': x.hostname,
                            }
                        )

                res = self.session.request(**self.fargs , **kwargs)

                res.raise_for_status ()

                self.referer1 = res.url
                
                x = dogs.fill_form (
                        res.text,
                        res.url,
                        flags = dogs.FILL_FLG_EXTRAS,
                        data = {
                            self.ans: None
                            }
                        )


                self.nextq = x
           
            self.count = int ('' + self.nextq [self.dt0][self.qn])
            
            if self.count == self.stop:
                self.stop = False

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
            x = parse.urlparse (self.nextq ['url'])

            self.nextq [self.dt1 or self.dt0] = qst
            
            self.totscore = int ('0' + qst [self.score])

            kwargs.setdefault (
                    'headers',
                    {
                        'referer': self.referer1,
                        'host': x.hostname,

                        }
                    )

            res = self.session.request (**self.nextq, **kwargs)

            res.raise_for_status ()

            self.nextq.pop (self.dt1 or self.dt0)

            self.referer = res.url

            res = self.fetch ()

            if not res:
                return res

            self.nextq [self.dt1 or self.dt0] = res

            s = (int ('0' + res[self.score]) - self.totscore) == 1

            self.totscore = int ('0' + res[self.score])

            return int (s)
            


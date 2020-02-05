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

        def __init__ (self, fargs, url, matno, tma , crscode, qmap, fb,
                stop = 10, session = requests):

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

            self.fargs = self._transform_req (fargs, matno, tma, crscode)

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
                    flags = dogs.FILL_FLG_EXTRAS,
                    data = {
                        self.ans: None
                        }
                    )

            self.count = int ('' + x [self.data][self.qn])
            self.nextq = x

            return x [self.data]
            

        def _copycase (self, repl):
            def __copycase(m):
                return repl.upper () if m['cs'].isupper () else repl.lower ()

            return __copycase


        def reconfigure (self, matno, tma , crscode):


            self.fargs = self._transform_req (self.fargs, matno, tma, crscode)
            return self

        def submit (self, qst, **kwargs):
            x = parse.urlparse (self.nextq ['url'])

            self.nextq.update (qst)

            kwargs.setdefault (
                    'headers',
                    {
                        'referer': self.referer1,
                        'host': '%s://%s' % (x.scheme, x.hostname),

                        }
                    )

            res = self.session.request (**nextq, **kwargs)

            res.raise_for_status ()

            self.referer = res.url

            res = _parse.search (self.fb, res.text)['result']

            self.score = int (res['score'])
            return int (res['mark'])
            



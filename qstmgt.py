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
import math
import requests
import copy

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


        def __init__ (self, nav, matno, tma , crscode, qmap, stop = 10):

            self.nav = nav
            to, fro = self.nav ('qst_page')[:-1]
            self.referer = fro.url

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

            self.fargs = self._transform_req (copy.deepcopy (to), matno, tma, crscode)

        def _transform_req (self, req, matno, tma , crscode):

            tma = str (tma)
            tma = 'tma' + tma if not tma.startswith (('tma', 'Tma', 'TMA')) else tma
            self.dt0 = 'data' if req['method'] in ('POST', 'post') else 'params'
            req['url'] = re.sub (r'(?P<cs>nou)\d{9}', self._copycase (matno), req['url'], flags = re.IGNORECASE)

            req['url'] = re.sub (r'(?P<cs>[A-Za-z]{3})\d{3}(?!\d+)',
                    self._copycase (crscode), req['url'], flags = re.IGNORECASE)

            req['url'] = re.sub (r'(?P<cs>tma)[1-3]', self._copycase(tma), req['url'], flags = re.IGNORECASE)


            for k in req.get(self.dt0, {}):
                req[self.dt0][k] = re.sub (r'(?P<cs>nou)\d{9}', self._copycase (matno), req[self.dt0][k], flags = re.IGNORECASE)

                req[self.dt0][k] = re.sub (r'(?P<cs>[A-Za-z]{3})\d{3}(?!\d+)',
                        self._copycase (crscode), req[self.dt0][k], flags = re.IGNORECASE)

                req[self.dt0][k] = re.sub (r'(?P<cs>tma)[1-3]',
                        self._copycase(tma), req[self.dt0][k], flags = re.IGNORECASE)

            return req


        def fetch (self, url1 = None, force = False, **kwargs):
            if force or (self.dt1 or self.dt0) not in self.nextq:
                self.fargs.update (url = url1 or self.fargs['url'])

                kwargs.setdefault (
                        'headers',
                        dogs.mkheader (self.fargs ['url'], self.referer)
                        )

                self.qres = self.nav.session.request(**self.fargs , **kwargs)

                self.referer1 = self.qres.url
                try:
                    self.qres.raise_for_status ()
                    self.nextq = dogs.fill_form (
                            self.qres.text,
                            self.qres.url,
                            flags = dogs.FILL_FLG_EXTRAS,
                            data = {
                                self.qmap ['ans']: None
                                }
                            )

                except:
                    return None

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

            self.nextq [self.dt1 or self.dt0] = qst

            self.totscore = math.trunc (int (qst [self.qmap ['score']] + '0') / 10)

            kwargs.setdefault (
                    'headers',
                    dogs.mkheader (self.nextq ['url'], self.referer1)
                    )

            self.sres = self.nav.session.request (**self.nextq, **kwargs)

            self.sres.raise_for_status ()
            x = self.nextq.pop (self.dt1 or self.dt0)

            self.referer = self.sres.url
            try:
                res = self.fetch ()

                self.nextq [self.dt1 or self.dt0] = res

                s = (math.trunc (int (res[self.qmap ['score']] + '0') / 10) - self.totscore) == 1

                self.totscore = math.trunc (int (res[self.qmap ['score']] + '0') / 10)

                return int (s)

            except:
                return None

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

UNKNOWN_COURSE = False
UNKNOWN_QST = None

class TmadogUtils (object):
    
    QstDbT = collections.namedtuple ('QstDbT', 'qdescr, ans, qid, crscode')

    #CrsDbT = collections.namedtuple ('CrsDbT', 'crscode, qid, answered', defaults = [False])

    #__all__ = ['submit', 'hack', 'scrape_tmaQ']

    class QMiter (object):

        def __init__ (self, miter):
            self.miter = miter

        def __iter__ (self):

            yield from self.__next__ ()

        def __next__ (self):

            for m in self.miter:
                if not re.fullmatch (r'\s+',m['qdescr']) and not re.fullmatch (r'\s+', m['ans']):
                    yield QstDbT (m['qdescr'].strip (), m['ans'].strip (),
                            m['qid'].strip (), m['crscode'].strip ())



    def submitter (
            ans_mgr,
            qst_mgr
            ):

        try:
            qst = qst_mgr.fetch ()

            while qst:
                
                qst = ans_mgr.answer (qst)
                if qst:
                    ans_mgr.check (
                            qst,
                            qst_mgr.submit (qst)
                        )

                elif qst is UNKNOWN_COURSE:
                    raise TypeError ('This course is Unknown', qst)

                elif qst is UNKNOWN_QST:
                    pass

                qst = qst_mgr.fetch ()

        except builtins.BaseException as err:
            print ('submitter: %s' % (err.args[0],))

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


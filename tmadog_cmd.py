import tmadog_utils
import sqlite3
import re
import requests
import dogs
import builtins
import random
import lxml
from pathlib import PurePath


#__all__ = ['submit', 'hack', 'scrape_tmaQ']

class QMiter (object):

    def __init__ (self, miter):
        self.miter = miter

    def __iter__ (self):

        for m in self.miter:
            if not re.fullmatch (r'\s+',m['qdescr']) and not re.fullmatch (r'\s+', m['ans']):
                yield tmadog_utils.QstDbT (m['qdescr'].strip (), m['ans'].strip (),
                        m['qid'].strip (), m['crscode'].strip ())

    def __next__ (self):
        
        for m in self.miter:
            if not re.fullmatch (r'\s+',m['qdescr']) and not re.fullmatch (r'\s+', m['ans']):
                return tmadog_utils.QstDbT (m['qdescr'].strip (), m['ans'].strip (),
                        m['qid'].strip (), m['crscode'].strip ())


TMADOGDB = 'tmadogdb'

def scraper_submitter_net (
        url,
        session,
        stp = 10, 
        mode = tmadog_utils.NORM, 
        **kwargs
        ):

    dt = []

    try:
        fetch = tmadog_utils.fetchtma (url, session = session, **kwargs) 

        qst, url = fetch()
        dt.append (qst.copy())
        getans = tmadog_utils.get_answer (TMADOGDB, qst, mode)
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
        fetch = tmadog_utils.fetchtma (rl, **kwargs) 
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

    dt = []

    try:
        fetch = tmadog_utils.fetchtma (url, session = session, **kwargs) 

        qst, url = fetch()
        qn = 1 
        cur = tmadog_utils.setupdb (db).cursor ()
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


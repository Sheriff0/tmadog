import tmadog_utils
import sqlite3
import re
import requests
import dogs
import builtins
import random
from pathlib import PurePath


#__all__ = ['submit', 'hack', 'scrape_tmaQ']

TMADOGDB = 'tmadogdb'

def hack_submit_tma (url, session, stp = 10, db = TMADOGDB, **kwargs):

    dt = []

    try:
        fetch = tmadog_utils.fetchtma (url, session = session, **kwargs) 

        qst, url = fetch()
        dt.append (qst.copy())
        ansraw = tmadog_utils.get_answer (TMADOGDB, qst, tmadog_utils.HACK)
        qn = int ('0' + qst['qj']) # Just in case it's empty

        while 1 <= qn <= stp:
            qst.update (ansraw)
            kont = session.post (url, data = dict (qst), headers = {
                'referer': url,
                }) 
            kont.raise_for_status ()

            qpage = session.send (
                    requests.Request (
                        ** dogs.click(
                            kont.text,
                            ltext = 'continue',
                            url = kont.url
                            ),

                        headers = {
                            'referer': kont.url
                            }
                        ).prepare ()
                    )

            if isinstance (qpage, requests.Response):
                qpage.raise_for_status ()

                qarg = dogs.fill_form(
                        qpage.text,
                        url = qpage.url, 
                        data = {'ans': None}
                        )

                qst = qarg['data']

                qn = int ('0' + qst['qj'])

                dt.append (qst.copy ())
                url = qarg['url']

            else:
                break

        if len (dt):
            return tmadog_utils.update_hacktab(db, dt)

    except builtins.BaseException as err:
        if len (dt):
            tmadog_utils.update_hacktab(db, dt)
        print (err.args[0])
        return -1


def scrapetma_net (db = TMADOGDB, **kwargs):
    rl = kwargs.pop ('rl', None)

    crscode = kwargs.get ('crscode', None)

    dt = []
    nqst = kwargs.pop ('nqst', 1)
    try:
        fetch = tmadog_utils.fetchtma (rl, **kwargs) 
        while nqst:
            m = fetch()[0]
            dt.append (m)
            nqst -= 1

        if len (dt):
            return tmadog_utils.update_hacktab(db, dt)

    except builtins.BaseException as err:
        if len (dt):
            tmadog_utils.update_hacktab(db, dt)
        print (err.args[0])
        return -1


def scrapetma_regex_f (
        fstr, 
        fpat = r'qtn\s*:.*?\n(?P<qdescr>.+?)^\W*ans\s*:.*?\n(?P<ans>.+?)(?P<qid>)(?P<crscode>)\n',
        db = TMADOGDB,
        enc = 'utf-8',
        flags = re.MULTILINE | re.IGNORECASE | re.DOTALL):

    if isinstance (fstr, PurePath):
        try:
            f = open (str (fstr), 'rt', encoding = enc)

            fstr = f.read ()

        except UnicodeDecodeError:
            f.reconfigure (encoding = 'utf-16le')
            f.seek (0)

            fstr = f.read ()

        except :
            return -1

        f.close ()

    return tmadog_utils.updatedb (db, [ m.groupdict () for m in re.finditer
        (fpat, fstr, flags = flags ) if not re.fullmatch (r'\s+',m['qdescr'])
        and not re.fullmatch (r'\s+', m['ans']) ])



def scrapetma_htmlstr (html, db = TMADOGDB, ans = None):
    try:    
        m = dogs.fill_form (
                html, 
                'https://foo/foo.html', 
                flags = dogs.NO_TXTNODE_KEY | dogs.NO_TXTNODE_VALUE | dogs.DATAONLY,
                data = { 'ans': ans }
                )
    except:
        return -1

    return tmadog_utils.update_hacktab(db, [ m ])


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



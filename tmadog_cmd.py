import tmadog_utils
import sqlite3
import re
import requests
import dogs
import builtins


__all__ = ['submit', 'hack', 'scrape_tmaQ']

TMADOGDB = 'tmadogdb'

def hack_submit_tma (url, session, stp = 10, db = TMADOGDB, **kwargs):

    dt = []

    try:
        fetch = tmadog_utils.fetchtma (url, session = session, **kwargs) 

        qst, url2 = fetch()
        dt.append (qst.copy())
        ansraw = tmadog_utils.get_answer (TMADOGDB, qst, tmadog_utils.HACK)
        qn = int (qst['qj'])

        while qn <= stp:
            qst.update (ansraw)
            kont = session.post (url2, data = qst, headers = {
            'referer': url,
            }) 
            kont.raise_for_status ()

            qpage = dogs.click(kont.text, ltext = 'continue', url = kont.url,
            session = session)

            if isinstance (qpage, requests.Response):
                qpage.raise_for_status ()

                qst = dogs.fill_form(qpage.text, url = qpage.url, flags =
                   dogs.NO_TXTNODE_KEY | dogs.NO_TXTNODE_VALUE | dogs.DATAONLY,
                   data = {'ans': None})
                qn = int (qst['qj'])

                dt.append (qst.copy ())

                url = dogs.fill_form(qpage.text, url = qpage.url, flags =
                   dogs.URLONLY)
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
        rl, 
        fpat =
        r'qtn\s*:.*?\n(?P<qdescr>.+?)^\W*ans\s*:.*?\n(?P<ans>.+?)(?P<qid>(?P=qdescr))?(?P<crscode>(?P=ans))?\n',
        db = TMADOGDB,
        enc = 'utf-8',
        flags = re.MULTILINE | re.IGNORECASE | re.DOTALL):

    fstr = ''

    try:
        f = open (rl, 'rt', encoding = enc)

    except UnicodeDecodeError:
        f = open (rl, 'rt', encoding = 'utf-16le')

    except :
        return -1

    fstr = f.read ()

    f.close ()

    return tmadog_utils.updatedb (db, [ m.groupdict () for m in re.finditer
        (fpat, fstr, flags = flags ) if not re.fullmatch (r'\s+',m['qdescr'])
        and not re.fullmatch (r'\s+', m['ans']) ])



def scrapetma_f_net (html, db = TMADOGDB):
        
    m = dogs.fill_form (
            html, 
            'https://foo/foo.html', 
            flags = dogs.NO_TXTNODE_KEY | dogs.NO_TXTNODE_VALUE | dogs.DATAONLY,
            data = { 'ans': None }
            )
    return tmadog_utils.update_hacktab(db, [ m ])

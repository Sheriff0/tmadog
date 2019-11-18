import tmadog_utils
import sqlite3
import re
import requests
import dogs
import builtins


__all__ = ['submit', 'hack', 'scrape_tma']


TMADOGDB = 'tmadogdb'

#def hack (url, token, session, trojan):
#
#
#def submit (reqobj, tma_token, session, ansfile):
#    qst = session.send (session.prepare_request (reqobj))
#    
#    query = tmadog_utils.get_query (qst.text)

#def hack_submit_tma ()

def scrape_tma (db = TMADOGDB, **kwargs):
    rl = kwargs.pop ('rl', None)

    crscode = kwargs.pop ('crscode', None)

    kwargs['crscode'] = crscode

    if rl and rl.startswith ('http'):
        dt = []
        nqst = kwargs.pop ('nqst', 1)
        try:
            fetch = tmadog_utils.fetchtma (rl, **kwargs) 
            while nqst:
                m = fetch()
                dt.append (m)
                nqst -= 1

            if len (dt):
                return tmadog_utils.updatedb(db, dt)

        except builtins.BaseException as err:
            if len (dt):
                tmadog_utils.updatedb(db, dt)
            print (err.args[0])
            return -1

    elif not rl:
        html = kwargs.pop ('html', None)
        if html:
            m = dogs.fill_form (
                    html, 
                    'https://foo/foo.html', 
                    flags = dogs.NO_TXTNODE_KEY | dogs.NO_TXTNODE_VALUE | dogs.DATAONLY,
                    data = { 'ans': None }
                    )
            return tmadog_utils.updatedb(db, [ m ])

    else:
        fstr = ''
        try:
            with open (rl, 'rt') as f:
                fstr = f.read ()

        except UnicodeDecodeError:
            with open (rl, 'rt', encoding = 'utf-16le') as f:
                fstr = f.read ()

        except :
            return -1

        fpat = r'qtn\s*:.*?\n(.+?)^\W*ans\s*:.*?\n(.+?)\n' 


        return tmadog_utils.updatedb (db, [ dict (qdescr = m[0], ans = m[1],
            crscode = crscode, qid = None) for m in
            re.findall (fpat, fstr, flags = re.MULTILINE | re.IGNORECASE
                | re.DOTALL ) if not re.fullmatch (r'\s+',m[0]) and not
            re.fullmatch (r'\s+', m[1]) ])

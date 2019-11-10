import tmadog_utils
import sqlite3
import re
import requests
import dogs


__all__ = ['submit', 'hack', 'scrape_tma']


TMADOGDB = 'tmadogdb'

#def hack (url, token, session, trojan):
#
#
#def submit (reqobj, tma_token, session, ansfile):
#    qst = session.send (session.prepare_request (reqobj))
#    
#    query = tmadog_utils.get_query (qst.text)


def scrape_tma (rl, db = TMADOGDB, **kwargs):

    repeats = 0
    conn = sqlite3.connect (db)

    try:
        conn.execute ('''SELECT * from questions;''')

    except sqlite3.OperationalError:
        conn.execute ('''CREATE TABLE questions (dogid INTEGER PRIMARY KEY
            AUTOINCREMENT, qdescr VARCHAR NOT NULL UNIQUE, ans VARCHAR, nouid CHAR);''')


    if rl.startswith ('http'):
        session = kwargs.pop ('session', requests.Session())

        headers = kwargs.pop ('headers', None)

        matno = kwargs.pop ('matno', None)
        crscode = kwargs.pop ('crscode', None)
        tma = kwargs.pop ('tma', 1)

        samplehtml = kwargs.pop ('html', None)
        nqst = int (kwargs.pop ('nqst', 1))
        
        if matno and crscode and samplehtml:
            
            req = dogs.dogs.fill_form(samplehtml, url = rl, flags = 3, idx=0,
                    nonstdtags =['button'], headers = headers)
            
            v = ''

            for k in req.data:
                if re.search (r'nou\d{9}', req.data[k], flags = re.IGNORECASE):
                    v = req.data[k]
                    break

            v = re.sub (r'nou\d{9}', matno.upper(), v, flags = re.IGNORECASE)
            v = re.sub (r'\w{3}\d{3}(\D)', crscode.upper() + r'\1', v, count =
                    1, flags = re.IGNORECASE)

            v = re.sub (r'tma[1-3]', 'TMA' + str (tma), v, flags = re.IGNORECASE)
            req.data[k] = v


            while nqst:
                    res = session.post(req.url, data = req.data, headers =
                            req.headers)
    #                res.raise_for_status ()
                    return res

                    m = tmadog_utils.get_query (res.text)
                    if m :
                        try:
                            conn.execute ('''INSERT INTO questions (qdescr) VALUES (?);''', ('+'.join (m.strip ().split ()),))

                        except sqlite3.IntegrityError:
                            repeats += 1
                    else:
                        return res
                
                    nqst -= 1

    else:
        try:
            with open (rl, 'rt') as f:
                fstr = f.read ()

        except UnicodeDecodeError:
            with open (rl, 'rt', encoding = 'utf-16le') as f:
                fstr = f.read ()

        except :
            return -1

        fpat = r'qtn\s*:.*?\n(.+?)ans\s*:.*?\n(.+?)\n' 


        for m in re.finditer (fpat, fstr, flags = re.MULTILINE | re.IGNORECASE
                | re.DOTALL ):
            try:
                conn.execute ('''INSERT INTO questions (qdescr, ans) VALUES (?, ?);''', ('+'.join (m.group (1).strip ().split ()), '+'.join (m.group (2).strip ().split ())))

            except sqlite3.IntegrityError:
                repeats += 1

    conn.commit ()

    conn.close()

    if repeats > 0:
        print ('%d questions repeated' % (repeats,))

    return None

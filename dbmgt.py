class DbMgt (object):

    TMADOGDB = 'tmadogdb'

    def setupdb (db):

        conn = sqlite3.connect (db)

        try:
            conn.executescript ('''
            CREATE TABLE IF NOT EXISTS questions (dogid INTEGER PRIMARY KEY
                    AUTOINCREMENT, qdescr VARCHAR NOT NULL UNIQUE);

            CREATE TABLE IF NOT EXISTS courses (cid INTEGER PRIMARY KEY
                    AUTOINCREMENT, crscode CHAR(6) DEFAULT NULL, dogid INTEGER NOT
                    NULL REFERENCES questions (dogid) MATCH FULL ON DELETE CASCADE ON
                    UPDATE CASCADE, ready BOOLEAN DEFAULT FALSE, qid CHAR);

            CREATE TABLE IF NOT EXISTS answers (ans VARCHAR DEFAULT NULL, dogid INTEGER
                    NOT NULL REFERENCES questions (dogid) MATCH FULL ON DELETE
                    CASCADE ON UPDATE CASCADE, cid INTEGER UNIQUE DEFAULT NULL
                    REFERENCES courses (cid) MATCH FULL ON DELETE CASCADE ON
                    UPDATE CASCADE);

            CREATE TABLE IF NOT EXISTS hacktab (cid INTEGER NOT NULL UNIQUE
            REFERENCES courses (cid),
            opta VARCHAR NOT NULL,
            optb VARCHAR NOT NULL,
            optc VARCHAR NOT NULL,
            optd VARCHAR NOT NULL);
                    ''')

            conn.commit ()
        except sqlite3.OperationalError as err:
            print ('create: ',err.args[0])
            conn.close ()
            return None

        return conn


    def update_hacktab (db, data, qmap, cursor = None):

        conn = setupdb (db) if not cursor else cursor.connection

        conn.row_factory = sqlite3.Row

        if not conn:
            return -1

        cur = conn.cursor ()

        ierr = None

        dogid, cid, = None, None

        for datum in data:
            try:
                crsref = cur.execute ('''
                        SELECT * FROM courses WHERE qid = ? AND crscode = ?
                        ;''', (
                            datum[qmap ['qid']],
                            datum[qmap ['crscode']]
                            )).fetchone ()

                if not crsref:
                    cid = updatedb (db, [datum], qmap, cur)['cid']

                else:
                    cid = crsref['cid']

                cur.execute ('''
                        REPLACE INTO hacktab (cid, opta, optb, optc, optd) VALUES (?, ?,
                        ?, ?, ?);
                        ''', (
                            cid,
                            datum[qmap ['a']],
                            datum[qmap ['b']],
                            datum[qmap ['c']],
                            datum[qmap ['d']]
                            ))
                if cursor:
                    return cursor

            except sqlite3.OperationalError as err:
                print ('update_hacktab: replace: ', err.args[0])
                conn.close ()
                return -1

        try:
            conn.commit ()

        except sqlite3.OperationalError as err:
            print (err.args[0])
            return conn

        return None


    def updatedb (db, data, qmap, cursor = None):

        repeats = 0

        conn = setupdb (db) if not cursor else cursor.connection

        conn.row_factory = sqlite3.Row

        if not conn:
            return -1

        cur = conn.cursor ()

        dogid, cid, = None, None

        ids = {}

        for datum in set (data):

            try:

                if isinstance (datum, QstDbT):
                    datum = datum._asdict ()
                cur.execute ('''INSERT INTO questions (qdescr)
                        VALUES (?);''', (datum[qmap ['qdescr']],))

                dogid = cur.lastrowid
                ids['dogid'] = dogid

                cur.execute ('''INSERT INTO courses (crscode, dogid, ready,
                qid) VALUES
                        (?, ?, ?, ?)''', (
                            datum[qmap ['crscode']],
                            dogid,
                            True if datum[qmap ['ans']] and datum[qmap ['crscode']] and datum[qmap ['qid']] else
                            False,
                            datum[qmap ['qid']]
                            ))

                cid = cur.lastrowid
                ids['cid'] = cid

                cur.execute ('''
                        INSERT INTO answers (ans, dogid, cid) VALUES (?, ?,
                        ?);
                        ''', (
                            datum[qmap ['ans']],
                            dogid,
                            cid
                            ))

                if cursor:
                    return ids

            except sqlite3.IntegrityError as ierr:

                repeats += 1

                dupq = cur.execute ('SELECT * FROM questions WHERE qdescr = ?', (datum[qmap ['qdescr']],)).fetchone ()

                crsref = cur.execute ('''
                        SELECT * FROM courses WHERE (crscode = ? AND qid = ? AND
                        dogid = ?) OR (dogid = ? AND ready = ?) LIMIT 1
                        ''', (
                            datum[qmap ['crscode']],
                            datum[qmap ['qid']],
                            dupq['dogid'],
                            dupq['dogid'],
                            False
                            )).fetchone() or {
                                    'cid': None,
                                    'dogid': dupq['dogid'],
                                    'crscode': None,
                                    'ready': False,
                                    'qid': None
                                    }

                ansref = cur.execute ('''SELECT * FROM answers WHERE (dogid =
            ? AND cid = ?) OR dogid = ?;''', (
                dupq['dogid'],
                crsref['cid'],
                dupq['dogid']
                )).fetchone () or {
                        'ans': None,
                        'dogid': None,
                        'cid': None
                        }

                cur1 = cur.connection.cursor ()

                cur1.execute ('''
                        REPLACE INTO courses (cid, crscode, dogid, ready, qid)
                        VALUES (?, ?, ?, ?, ?)
                        ''', (
                            crsref['cid'],
                            datum[qmap ['crscode']] or crsref['crscode'],
                            crsref['dogid'],
                            True if (ansref['ans'] or datum[qmap ['ans']]) and (datum[qmap ['qid']] or
                                crsref['qid']) and (crsref['crscode'] or
                                    datum[qmap ['crscode']]) else False,
                                datum[qmap ['qid']] or crsref['qid']
                                ))

                cid = cur1.lastrowid

                ids['cid'] = cid

                ids['dogid'] = dupq['dogid']

                cur.execute ('''
                        REPLACE INTO answers (ans, dogid, cid) VALUES (?,
                        ?, ?)
                        ''', (
                            datum[qmap ['ans']] or ansref['ans'],
                            dupq['dogid'],
                            cid
                            ))

                if cursor:
                    return ids

            except sqlite3.OperationalError as err:
                print ('insert/replace: ', err.args[0])
                conn.close ()
                return -1

        try:
            conn.commit ()

        except sqlite3.OperationalError as err:
            print (err.args[0])
            return conn

        if not cursor:
            conn.close()
        else:
            return cursor

        if repeats > 0:
            print ('%d questions repeated' % (repeats,))

        return None



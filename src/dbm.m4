import sqlite3
import json

def setupdb (db):

    conn = sqlite3.connect (db)

    try:
        conn.executescript ("""
        CREATE TABLE IF NOT EXISTS questions (dogid INTEGER PRIMARY KEY
                AUTOINCREMENT, qdescr VARCHAR NOT NULL UNIQUE);

        CREATE TABLE IF NOT EXISTS courses (cid INTEGER PRIMARY KEY
                AUTOINCREMENT, crscode CHAR(6) DEFAULT NULL, dogid INTEGER NOT
                NULL REFERENCES questions (dogid) MATCH FULL ON DELETE CASCADE ON
                UPDATE CASCADE, ready BOOLEAN DEFAULT FALSE, qid CHAR);

        CREATE TABLE IF NOT EXISTS answers (ans VARCHAR DEFAULT NULL, dogid INTEGER
                NOT NULL REFERENCES questions (dogid) MATCH FULL ON DELETE
                CASCADE ON UPDATE CASCADE, cid INTEGER PRIMARY KEY NOT NULL
                REFERENCES courses (cid) MATCH FULL ON DELETE CASCADE ON
                UPDATE CASCADE);

        CREATE TABLE IF NOT EXISTS hacktab (cid INTEGER NOT NULL PRIMARY KEY
        REFERENCES courses (cid),
        opta VARCHAR NOT NULL,
        optb VARCHAR NOT NULL,
        optc VARCHAR NOT NULL,
        optd VARCHAR NOT NULL);
                """)

        conn.commit ()
    except sqlite3.OperationalError as err:
        print ("create: ",err.args[0])
        conn.close ()
        return None

    return conn


def update_qca_tab (db, data, qmap, cursor = None):

    repeats = 0

    conn = setupdb (db) if not cursor else cursor.connection

    conn.row_factory = sqlite3.Row

    if not conn:
        return -1

    cur = conn.cursor ()

    dogid, cid, = None, None

    ids = {}

    for datum in data:

        try:

            cur.execute ("""INSERT INTO questions (qdescr)
                    VALUES (?);""", (datum[qmap ["qdescr"]],))

            dogid = cur.lastrowid
            ids["dogid"] = dogid

            cur.execute ("""INSERT INTO courses (crscode, dogid, ready,
            qid) VALUES
                    (?, ?, ?, ?)""", (
                        datum[qmap ["crscode"]],
                        dogid,
                        True if datum[qmap ["ans"]] and datum[qmap ["crscode"]] and datum[qmap ["qid"]] else False,
                        datum[qmap ["qid"]]
                        ))

            cid = cur.lastrowid
            ids["cid"] = cid

            cur.execute ("""
                    INSERT INTO answers (ans, dogid, cid) VALUES (?, ?,
                    ?);
                    """, (
                        datum[qmap ["ans"]],
                        dogid,
                        cid
                        ))


        except sqlite3.IntegrityError as ierr:

            repeats += 1

            dupq = cur.execute ("SELECT * FROM questions WHERE qdescr = ?", (datum[qmap ["qdescr"]],)).fetchone ()

            crsref = cur.execute ("""
                    SELECT * FROM courses WHERE (crscode == ? AND qid == ? AND
                    dogid == ?) OR (dogid == ? AND crscode = ?) LIMIT 1
                    """, (
                        datum[qmap ["crscode"]],
                        datum[qmap ["qid"]],
                        dupq["dogid"],
                        dupq["dogid"],
                        None,
                        )).fetchone()

            cur1 = cur.connection.cursor ()

            cur1.execute ("""
                    REPLACE INTO courses (cid, crscode, dogid, ready, qid)
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        crsref["cid"] if crsref else None,
                        datum[qmap ["crscode"]],
                        dupq ["dogid"],
                        True if datum[qmap ["ans"]] and datum[qmap ["qid"]] and datum[qmap ["crscode"]] else False,
                            datum[qmap ["qid"]]
                            ))

            cid = cur1.lastrowid

            ids["cid"] = cid

            ids["dogid"] = dupq["dogid"]

            cur.execute ("""
                    REPLACE INTO answers (ans, dogid, cid) VALUES (?,
                    ?, ?)
                    """, (
                        datum[qmap ["ans"]],
                        dupq["dogid"],
                        cid
                        ))

        except sqlite3.OperationalError as err:
            print ("insert/replace: ", err.args[0])
            conn.close ()
            return -1

    conn.commit ()

    if cursor:
        return ids

    else:
        if repeats > 0:
            print ('%d questions repeated' % (repeats,))


        return None


def update_hacktab (db, data, qmap, cursor = None, fp = None):

    conn = setupdb (db) if not cursor else cursor.connection

    conn.row_factory = sqlite3.Row

    if not conn:
        return -1

    cur = conn.cursor ()

    if fp:
        fp.write ('[')

    ierr = None

    arr = []

    dogid, cid, = None, None

    for datum in data:

        if fp:
            arr.append (datum)

        try:
            cid = update_qca_tab (db, [datum], qmap, cur)["cid"]

            cur.execute ("""
                    REPLACE INTO hacktab (cid, opta, optb, optc, optd) VALUES (?, ?,
                    ?, ?, ?);
                    """, (
                        cid,
                        datum[qmap ["opta"]],
                        datum[qmap ["optb"]],
                        datum[qmap ["optc"]],
                        datum[qmap ["optd"]]
                        ))


        except sqlite3.OperationalError as err:
            conn.close ()
            print ("update_hacktab: replace: ", err.args[0])

    if arr and fp:
        json.dump (arr, fp)

    try:
        conn.commit ()

    except sqlite3.OperationalError as err:
        print (err.args[0])
        return conn

    if cursor:
        return cursor
    else:
        return None

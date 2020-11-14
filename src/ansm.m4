changequote`'include(`module.m4')dnl
#changequote`'include(`utils.m4')changequote`'dnl
import re
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
import copy
ifdef(
`LIBPREFIX',
`dnl
import strip(LIBPREFIX)`'dbm
import strip(LIBPREFIX)`'dogs
',
`dnl
import dbm
import dogs
'dnl
)dnl

ANS_MODE_MAD = 0b00
ANS_MODE_HACK = 0b01
ANS_MODE_NORM = 0b10

ANS_NOANSWER = -1
ANS_NOCOURSE = 0
ANS_FAIL = -2

class AnsMgr (object):

ifdef(
`CONFIG_POLICE',
`dnl
    prologs = [
                """The course {crscode} is unknown to the database, can you answer this question of it?""",


                """I failed the answer to this question. Please can you answer it ?""",

                """This question has no answer in the database, can you answer it?""",
    ]

    epilogs = [
            "",

            """Type "%s" if answer corresponds to row %s and so on.""",

            """Type "%s" if answer corresponds to row %s or type ":hack" to switch to hack mode."""
            ]

    def __init__ (self, qmap, database, mode, pseudo_ans, interactive = True, max_retry = 3,):
        self.interactive = interactive
        self.max_retry = max_retry
',
`dnl
    def __init__ (self, qmap, database, mode, pseudo_ans,):
'dnl
)dnl
        self.pseudos = pseudo_ans
        self.mode = mode
        self.database = database
        self._cache = {}
        self._cur = None
        self.qmap = qmap

    class CacheIter (object):
        def __init__ (self, cache, qmap, reverser):
            self.cache = cache
            self.revert_ans = reverser
            self.qmap = qmap

        def __iter__ (self):
            yield from self.__next__ ()

        def __next__ (self):

            for v in self.cache.values ():
                if self.qmap ["qdescr"] not in v:
                    for v1 in v.values ():
                        yield self.revert_ans (v1)

                else:
                    yield self.revert_ans (v)



    def __call__ (self, crscode, qid, strict = True):
        x = self._cache.get (qid, None)

        if x:
            if x.get (self.qmap ["crscode"], None) == crscode:
                return x

            else:
                x = self._cache.get (crscode, None)
                y = x.get (qid, None) if x else x
                if y:
                    return y

                elif not strict:
                    if x:
                        for v in x.values ():
                            return v

                else:
                    return None

    def pop (self, crscode, qid, *fallback):
        x = self._cache.pop (qid, None)

        if x:
            if x.get (self.qmap ["crscode"], None) == crscode:
                return x

            else:
                self._cache.setdefault (qid, x)
                x = self._cache.get (crscode, None)
                y = x.pop (qid, None) if x else x
                if y:
                    return y
                else:
                    if fallback:
                        return fallback [0]
                    raise KeyError (crscode, qid)


    def get (self, crscode, qid, *fallback):
        x = self._cache.get (qid, None)

        if x:
            if x.get (self.qmap ["crscode"], None) == crscode:
                return x

            else:
                self._cache.setdefault (qid, x)
                x = self._cache.get (crscode, None)
                y = x.get (qid, None) if x else x
                if y:
                    return y
                else:
                    if fallback:
                        return fallback [0]
                    raise KeyError (crscode, qid)


    def _copycase (self, t, i):
        return i.upper () if t.isupper () else i.lower ()

ifdef(
`CONFIG_MODULE',
`dnl
    def _mkprompt (self):
        txt = """{prolog}

    {%s}. {%s}

    """ % (self.qmap ["qn"], self.qmap ["qdescr"])

        for i in range (len (self.pseudos)):
            k = "opt" + bytes ([65+i]).decode ()
            txt += "%s: {%s}\n" % (self.pseudos [i], self.qmap [k])

        txt += """
        {epilog}
        (type ":quit" to quit and leave question unanswered) --> """

        return txt

    def _qpromt (self, qst, epilog = None, prolog = None):

        if not hasattr (self, "p_text"):
            self.p_text = self._mkprompt ()

        x = input (self.p_text.format (
            prolog = prolog or "(tmadog)",
            epilog = epilog or """Type "%s" if answer corresponds to row %s and so on.""" % (self.pseudos[0], self.pseudos[0]),
            **qst
            )
            )

        return x


    def qprompt (self, qst, epilog = None, prolog = None, max_retry = 0,
            err_msg = None):

        x = self._qpromt (qst, epilog, prolog)
        try:
            qst [self.qmap ["ans"]] = self._copycase (self.pseudos[0], x) if not re.fullmatch (r"\s*", x) and not x.startswith (":") else None

        except ValueError:

            while max_retry:
                x = self._qpromt (
                        qst,
                        epilog,
                        (err_msg or """
    Error: You have entered an invalid option. %d attempt(s) left""") % ( max_retry, )
                        )
                try:
                    qst [self.qmap ["ans"]] = self._copycase (self.pseudos[0], x) if len (x) and not x.startswith (":") else None
                    break

                except ValueError:
                    pass

                max_retry -= 1


        finally:

            return x
',
`'dnl
)dnl

    def check (self, qst, mark, effective = None):
        if mark == 0:
            qst = qst.copy ()
ifdef(
`CONFIG_MODULE',
`dnl
            if not self.interactive:
                x = self (qst [self.qmap ["crscode"]], qst [self.qmap ["qid"]])

                if x and qst [self.qmap ["ans"]] == x [self.qmap ["ans"]]:
                    x [self.qmap ["ans"]] = None

                elif not x:
                    qst [self.qmap ["ans"]] = None
                    self.update (qst.copy ())

            else:
                return self.resolve (qst, self.FAIL)
',
`dnl
            x = self (qst [self.qmap ["crscode"]], qst [self.qmap ["qid"]])

            if x and qst [self.qmap ["ans"]] == x [self.qmap ["ans"]]:
                x [self.qmap ["ans"]] = None

            elif not x:
                qst [self.qmap ["ans"]] = None
                self.update (qst.copy ())
'dnl
)dnl

        elif mark == 1:
            self.update (qst.copy ())


    def answer (self, qst):

        try:
            qst [self.qmap ["ans"]] = chr (0)
            raise TypeError ("Question has no checking mechanism", type (qst))
        except:
            pass


        if self.mode & ANS_MODE_NORM:
            x = self (qst [self.qmap ["crscode"]], qst [self.qmap ["qid"]])

            if x and x[self.qmap ["ans"]]:
                qst [self.qmap ["ans"]] = x [self.qmap ["ans"]]

                self.update (qst)

                return qst

            else:

                x = self._fetch (qst)
                if x and x [self.qmap ["ans"]]:
                    x = self.convert_ans (qst, x[self.qmap ["ans"]])
                    if x:
                        qst [self.qmap ["ans"]] = x
                        self.update (qst)
                        return qst



        if self.mode & ANS_MODE_HACK:
            x = self (qst [self.qmap ["crscode"]], qst [self.qmap ["qid"]], strict = False) or self._hack (qst)

            if x and self.qmap ["crscode"] in x:
                self.update (qst)
                qst = self.download (x, qst)
                return qst

            elif x and x[self.qmap ["ans"]]:
                x = dict (x)
                x [self.qmap ["ans"]] = self.convert_ans (x, x[self.qmap ["ans"]])

                if x [self.qmap ["ans"]]:
                    self.update (qst)
                    qst = self.download (x, qst)
                    self.update (qst)
                    return qst


        self.resolve (qst, ANS_NOANSWER)

    def update (self, qst):

        qst = copy.deepcopy (qst)

        y = self._cache.get (qst [self.qmap ["qid"]], None)

        if y and (y [self.qmap ["qdescr"]] != qst [self.qmap ["qdescr"]] or y [self.qmap ["crscode"]] != qst [self.qmap ["crscode"]]):

            self._cache.setdefault (qst [self.qmap ["crscode"]], {})

            self._cache [qst [self.qmap ["crscode"]]].update ([(qst
                [self.qmap ["qid"]],
                    qst)])

        else:
            self._cache [qst [self.qmap ["qid"]]] = qst


    def resolve (self, qst, sig):
ifdef(
`CONFIG_MODULE',
`dnl
        if not self.interactive:
            self.update (qst)

            return sig

        x = self.qprompt (
                qst,
                prolog = self.prologs [sig].format (**qst),
                epilog = self.epilogs [ANS_MODE_NORM if self.mode > ANS_MODE_NORM else self.mode] % (self.pseudos[0], self.pseudos[0]),

                max_retry = self.max_retry
                )

        if x in (":hack", ":Hack", ":HACK"):
            self.mode = ANS_MODE_HACK

        self.update (qst.copy ())

        return None if not qst[self.qmap ["ans"]] else qst
',
`dnl

        self.update (qst)

        return sig
'dnl
)dnl

    def revert_ans (self, qst):
        qst = qst.copy ()

        if qst [self.qmap ["ans"]]:
            try:
                i = self.pseudos.index (qst [self.qmap ["ans"]])
                k = "opt" + chr (97 + i)
                qst [self.qmap ["ans"]] = qst [self.qmap [k]]

            except ValueError:
                pass

        return qst



    def convert_ans (self, qst, ans):
        ans = re.sub (r"\W+", r"\\W+?", ans.strip ())
        if not hasattr (self, "opts"):
            self.opts = [ "opt" + chr (97 + a) for a in range (len (self.pseudos))]

        for i in range (len (self.pseudos)):
            if re.match (ans, qst[self.qmap [self.opts [i]]].strip (), flags = re.IGNORECASE):
                return self.pseudos [i]

        return None


    def iter_cache (self):

        return self.CacheIter (self._cache, self.qmap, self.revert_ans)

    def close (self):

        self._cur.connection.commit ()

        self._cur.connection.close ()
        if hasattr (self, "mcur"):
            self.mcur.connection.commit ()
            self.mcur.connection.close ()

    def _hack (self, qst):

        if not self._cur:
            conn = dbm.setupdb (self.database)
            conn.row_factory = sqlite3.Row
            self._cur = conn.cursor ()

        self._cur.execute ("""
            SELECT qdescr AS %s, ans AS %s, qid AS %s, opta AS %s, optb AS
            %s, optc AS %s, optd AS %s FROM questions AS q INNER JOIN
            (courses AS c, answers AS a, hacktab AS h) ON (c.dogid ==
            q.dogid AND a.dogid == c.dogid AND c.ready IS NOT
                    ? AND crscode LIKE ? AND a.cid == c.cid AND h.cid ==
                    c.cid) LIMIT 1""" % (
                    self.qmap ["qdescr"],
                    self.qmap ["ans"],
                    self.qmap ["qid"],
                    self.qmap["opta"],
                    self.qmap["optb"],
                    self.qmap["optc"],
                    self.qmap["optd"]
                    ),
                (
                    False,
                    qst[self.qmap ["crscode"]],
                    )
                )

        a = self._cur.fetchone ()

        if not a:
            return self._mad (qst)
        else:
            return a


    def _mad (self, qst):

        if not hasattr (self, "mcur"):
            conn = dbm.setupdb (self.database)
            conn.row_factory = sqlite3.Row
            self.mcur = conn.cursor ()

            self.mcur.execute ("""
                SELECT qdescr AS %s, ans AS %s, qid AS %s, opta AS %s, optb AS
                %s, optc AS %s, optd AS %s FROM questions AS q INNER JOIN
                (courses AS c, answers AS a, hacktab AS h) ON (c.dogid ==
                q.dogid AND a.dogid == c.dogid AND c.ready IS NOT
                        ? AND a.cid == c.cid AND h.cid ==
                        c.cid) ORDER BY c.dogid DESC""" % (
                        self.qmap ["qdescr"],
                        self.qmap ["ans"],
                        self.qmap ["qid"],
                        self.qmap["opta"],
                        self.qmap["optb"],
                        self.qmap["optc"],
                        self.qmap["optd"]
                        ),
                    (
                        False,
                        )
                    )

        return self.mcur.fetchone ()


    def _fetch (self, qst):

        if not self._cur:
            conn = dbm.setupdb (self.database)
            conn.row_factory = sqlite3.Row
            self._cur = conn.cursor ()

        self._cur.execute ("""
        SELECT ans AS %s FROM answers INNER JOIN (courses) ON
        (courses.crscode LIKE ? AND courses.qid == ? AND courses.ready == ?
        AND answers.cid == courses.cid) LIMIT 1
                """ % (
                    self.qmap ["ans"],
                    ),
                (
                    qst [self.qmap ["crscode"]],
                    qst [self.qmap ["qid"]],
                    True,
                    )
                )

        r = self._cur.fetchone ()

        if not r:

            self._cur.execute ("""
            SELECT ans AS %s FROM answers INNER JOIN questions ON qdescr
            LIKE ? WHERE answers.dogid == questions.dogid AND answers.ans
            IS NOT ? LIMIT 1
                    """ % (
                        self.qmap ["ans"],
                        ),

                    (
                        qst [self.qmap ["qdescr"]],
                        None
                        )
                    )

            r = self._cur.fetchone ()

        return r

    def download (self, x, qst):

        if not hasattr (self, "opts"):
            self.opts = [ "opt" + chr (97 + a) for a in range (len (self.pseudos))]

        w = copy.deepcopy (qst)

        w.update (
                {
                    y: x [y] for y in (self.qmap [z] for z in self.qmap if z in ["qdescr", "qid", "ans"] + self.opts)
                    }
                )

        return w

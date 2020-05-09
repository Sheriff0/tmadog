from navigation import Navigation
from qstmgt import QstMgt
import cloudscraper
import curses
import math
import copy
import pdb
import cookie_parse
import requests

class QScrList (list):
    def index (self, value, attr = None, start = 0, stop = 2147483647):

        for i, item in zip (range (start, stop), self [start:stop]):
            if attr and hasattr (item, attr) and getattr (item, attr) == value:
                return i

            elif attr and hasattr (item, 'get') and item.get (attr, None) == value:
                return i

            elif not attr and value == item:
                return i

        raise ValueError ('QScrList: No item == %s' % (repr (value),) if not attr
                else 'QScrList: No item item.%s == %s' % (repr (attr), repr
                    (value)))


class Pscr:
    def __init__ (self, screen):
        self.screen = screen
    
    def acquire (self, vscr):
        self.vscr = vscr

    def __getitem__ (self, key):
        return getattr (self.screen, key)

    def __setitem__ (self, key, value):
        setattr (self.screen, key, value)

    def owner (self):
        if hasattr (self, 'vscr'):
            return self.vscr
        else:
            return None

    def release (self):
        self.vscr = None




class QScr:
    def __init__ (self, nav, qscr, matno, crscode, tma, id = None):
        self.nav = nav
        self.tma = tma
        self.crscode = crscode
        self.matno = matno
        self.qscr = qscr
        self.qmgr = None
        self.qline = 0
        self.optmap = []
        self.pqidx = None
        self.lpqidx = None
        self.id = id
        self.qst = None
        self.qmode = False


    def boot (self):
        if not self.qmgr:

            to, fro = self.nav ('qst_page')[:-1]
            self.qmgr = QstMgt.QstMgr (
                    matno = self.matno,
                    crscode = self.crscode,
                    tma = self.tma,
                    fargs = copy.deepcopy (to),
                    stop = 10,
                    url = fro.url,
                    qmap = self.nav.webmap ['qmap'],
                    session = self.nav.session

                    )
            
            self.qmgr.interactive = True

        return self.qmgr


    def acquire_screen (self, pscreen, scrparams = None):
        self.pscr = pscreen
        
        self.pscr.acquire (self)

        self.scord, self.scrdim = scrparams if scrparams else (self.pscr ['getbegyx'] (), self.pscr ['getmaxyx'] ())

    def has_screen (self):
        return hasattr (self, 'pscr') and self.pscr and self is self.pscr.owner ()

    def release_screen (self):
        if hasattr (self, 'pscr') and self.pscr and self is self.pscr.owner ():
            ret = [self.pscr, (self.scord, self.scrdim)]
            self.pscr.release ()
            return ret

    def resize (self, lines = None, cols = None):
        pass



class QscrMuxer:
    V_GRANULARITY = 1000

    def __init__ (self, pscreen, keys): 
        
        self.pscreen = pscreen

        scord, scrdim = self.pscreen.getbegyx (), self.pscreen.getmaxyx ()


        if scrdim [0] < 3:
            self.has_screen = False
            return -1
        
        else:
            self.has_screen = True
            d = 1
            if scrdim [0] == 3:
                self.qst_scr = self.pscreen
            else:
                d = min (2, len (keys))

                self.status_scr = self.pscreen.derwin (1, scrdim [1], 0, 0)

                self.status_bar = curses.newpad (1, self.V_GRANULARITY)

                self.qst_scr = self.pscreen.derwin (scrdim [0] - 1, scrdim [1], 1, 0)
                scord, scrdim = self.qst_scr.getbegyx (), self.qst_scr.getmaxyx ()


        minlines = math.trunc ((scrdim [0]) / d)

        self.subscreens = []

        for i in range (d):
            self.subscreens.append (
                    Pscr (self.qst_scr.derwin (minlines, scrdim [1], i *
                        minlines, 0))
                    )

        i += 1

        self.subscreens [-1] ['resize'] (minlines + (scrdim [0] - (i * minlines)), scrdim [1])

        self.vscreen = curses.newpad (self.V_GRANULARITY * len (keys), scrdim
                [1] - 2)

        qscrs = QScrList ()
        nav = None

        for i, key in enumerate (keys):
            pk = key [keys.MATNO]
            
            try:
                idx = qscrs.index (pk, attr = 'matno', start = 0, stop = i)
                nav = qscrs [idx].nav
                nav.refcount += 1

            except ValueError:

                nav = Navigation.Navigator (
                        key [keys.URL],
                        key [keys.WMAP], 
                        key,
                        session = self.mksess (key [keys.URL], key [keys.COOKIES])
                        )

            finally:

                qscrs.append (
                        QScr (
                            nav,
                            self.vscreen.derwin (self.V_GRANULARITY, scrdim [1] - 2, self.V_GRANULARITY * i, 0),
                            pk,
                            key [keys.CRSCODE],
                            key [keys.TMA],
                            id = i
                            )
                        )


        self.qscrs = qscrs

        self.qscr_len = len (keys)

        self.qscr_pointer = 0
        
        self.dimref = scrdim

        self.post_init ()


    def post_init (self):
        for i, pscr in enumerate (self.subscreens, self.qscr_pointer):
            self.qscrs [i].acquire_screen (pscr)

        self.load ()

    def replace (self, keys):
        pass

    def mksess (self, url, cookie_file = ''):
        session = None

        if cookie_file:
            with open (cookie_file) as f:
                cookie_str = f.read ()

                session = requests.Session ()
                cookt = cookie_parse.bake_cookies (cookie_str, url)

                session.headers = requests.structures.OrderedDict(
                        (
                            ("Host", None),
                            ("Connection", "keep-alive"),
                            ("Upgrade-Insecure-Requests", "1"),
                            ("User-Agent", cookt [0]['User-Agent']),
                            (
                                "Accept",
                                "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                                ),
                            ("Accept-Language", "en-US,en;q=0.9"),
                            ("Accept-Encoding", "gzip, deflate"),
                            )
                        )

                session.cookies = cookt [1]

        else:
            session = cloudscraper.create_scraper ()

        
        return session

    def __getitem__ (self, key):
        return getattr (self.qscrs [self.qscr_pointer], key)

    def __setitem__ (self, key, value):
        setattr (self.qscrs [self.qscr_pointer], key, value)


    def scroll (self, offset):

        p = self.qscr_pointer

        self.qscr_pointer += offset

        if self.qscr_pointer >= self.qscr_len:
            self.qscr_pointer = 0

        elif self.qscr_pointer < 0:
            self.qscr_pointer = self.qscr_len - 1

        if not self.qscrs [self.qscr_pointer].has_screen ():
            if self.qscrs [p].has_screen ():
                self.qscrs [self.qscr_pointer].acquire_screen (
                        *self.qscrs [p].release_screen ()
                        )

            else:
                self.qscr_pointer = p
                return -1

        self.load ()


    def load (self, scr = None):

        if scr == None:
            scr = self.qscrs [self.qscr_pointer]

        scr.boot ()

        self.scrdim = (scr.scrdim [0] - 2, scr.scrdim [1])
        self.scord = (scr.scord [0] , scr.scord [1])


        scr.pscr ['addnstr'] (self.scrdim [0], 0,
                '%s %s TMA%s' % (scr.matno.upper (), scr.crscode.upper (),
                    scr.tma), self.scrdim [1])

        scr.pscr ['chgat'] (self.scrdim [0], 0 ,
                curses.A_REVERSE)

        scr.pscr ['noutrefresh'] ()

        return self

    
    def resize (self, pscreen):
        self.pscreen = pscreen

        self.pscreen.clear ()

        scord, scrdim = self.pscreen.getbegyx (), self.pscreen.getmaxyx ()


        if scrdim [0] < 3:
            self.has_screen = False
            self.status_scr = None
            self.status_bar = None
            return -1
        
        else:
            self.has_screen = True
            d = 1
            if scrdim [0] == 3:
                self.qst_scr = self.pscreen
            else:
                d = min (2, self.qscr_len)

                self.status_scr = self.pscreen.derwin (1, scrdim [1], 0, 0)

                self.status_bar = curses.newpad (1, self.V_GRANULARITY)

                self.qst_scr = self.pscreen.derwin (scrdim [0] - 1, scrdim [1], 1, 0)
                scord, scrdim = self.qst_scr.getbegyx (), self.qst_scr.getmaxyx ()


        minlines = math.trunc ((scrdim [0]) / d)

        self.subscreens = []

        for i in range (d):
            self.subscreens.append (
                    Pscr (self.qst_scr.derwin (minlines, scrdim [1], i *
                        minlines, 0))
                    )

        i += 1

        self.subscreens [-1] ['resize'] (minlines + (scrdim [0] - (i * minlines)), scrdim [1])

        self.vscreen.resize (self.V_GRANULARITY * self.qscr_len,
                scrdim [1] - 2)

        ptr = self.qscr_pointer

        i = 0
        idx = None

        for scr in self.qscrs:
            scr.qscr.resize (self.V_GRANULARITY, scrdim [1] - 2)

            if scr.has_screen ():
                scr.release_screen ()
                #pdb.set_trace ()
                try:
                    s = self.subscreens [i]
                    scr.acquire_screen (s)
                    idx = scr.id
                    self.qscr_pointer = idx
                    yield (self.load (), scrdim [1] >= self.dimref [1])
                    i += 1

                except IndexError:
                    pass

        
        self.qscr_pointer = ptr
        if not self.qscrs [self.qscr_pointer].has_screen ():
            if self.qscrs [idx].has_screen ():
                self.qscrs [self.qscr_pointer].acquire_screen (
                        *self.qscrs [idx].release_screen ()
                        )

        yield (self.load (), scrdim [1] >= self.dimref [1])

        self.dimref = scrdim

        return



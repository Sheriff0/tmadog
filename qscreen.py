from navigation import Navigation
from qstmgt import QstMgt
import cfscrape
import curses
import math

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


class QScr:
    def __init__ (self, nav, qscr, matno, crscode, tma):
        self.nav = nav
        self.tma = tma
        self.crscode = crscode
        self.matno = matno
        self.qscr = qscr
        self.qmgr = None
        self.qline = 0
        self.pqidx = -1
        self.lpqidx = -1

    def __eq__ (self, value):
        return self.qscr == value

    def boot (self):
        if not self.qmgr:
            if 'tma_page:-1' not in self.nav:
                self.nav ('qst_page')[:-1]

            to, fro = self.nav ['qst_page:-1']
            self.qmgr = QstMgt.QstMgr (
                    matno = self.matno,
                    crscode = self.crscode,
                    tma = self.tma,
                    fargs = to,
                    stop = 10,
                    url = fro.url,
                    qmap = self.nav.webmap ['qmap'],
                    session = self.nav.session

                    )
            
            self.qmgr.interactive = True

        return self.qmgr

    def __getitem__ (self, attr):
        if self.has_screen ():
            return getattr (self.pscr, attr)

        else:
            raise Exception ('QScr: No available screen')


    def acquire_screen (self, pscreen, scrparams = None):
        self.pscr = pscreen

        self.scord, self.scrdim = scrparams if scrparams else (self.pscr.getbegyx (), self.pscr.getmaxyx ())

    def has_screen (self):
        return hasattr (self, 'pscr') and self.pscr

    def release_screen (self):
        ret = [self.pscr, (self.scord, self.scrdim)]
        self.pscr = None
        self.scord = self.scrdim = None
        return ret

    def resize (self, lines = None, cols = None):
        pass



class QscrMuxer:
    V_GRANULARITY = 10000
    MAX_PHY_SCREENS = 2

    def __init__ (self, pscreen, keys): 
        
        self.pscreen = pscreen

        scord, scrdim = self.pscreen.getbegyx (), self.pscreen.getmaxyx ()


        if scrdim [0] == 0:
            self.has_screen = False
            return -1
        
        else:
            self.has_screen = True
            d = 1
            if scrdim [0] == 1:
                self.qst_scr = self.pscreen
            else:
                if scrdim [0] > 2:
                    d = min (self.MAX_PHY_SCREENS, len (keys))

                self.status_scr = self.pscreen.derwin (1, scrdim [1], 0, 0)

                self.status_bar = curses.newpad (1, self.V_GRANULARITY)

                self.qst_scr = self.pscreen.derwin (scrdim [0] - 1, scrdim [1], 1, 0)
                scord, scrdim = self.qst_scr.getbegyx (), self.qst_scr.getmaxyx ()


        minlines = math.trunc ((scrdim [0]) / d)

        self.subscreens = []

        for i in range (d):
            self.subscreens.append (
                    self.qst_scr.derwin (minlines, scrdim [1], i * minlines, 0)
                    )

        i += 1

        self.subscreens [-1].resize (minlines + (scrdim [0] - (i * minlines)), scrdim [1])

        self.vscreen = curses.newpad (self.V_GRANULARITY * len (keys), scrdim
                [1] - 2)

        qscrs = QScrList ()

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
                        session = cfscrape.create_scraper ()
                        )

            finally:

                qscrs.append (
                        QScr (
                            nav,
                            self.vscreen.derwin (self.V_GRANULARITY, scrdim [1] - 2, self.V_GRANULARITY * i, 0),
                            pk,
                            key [keys.CRSCODE],
                            key [keys.TMA]
                            )
                        )


        self.qscrs = qscrs

        self.qscr_len = len (keys)

        self.qscr_pointer = 0

        self.post_init ()

    def post_init (self):
        for i, pscr in enumerate (self.subscreens, self.qscr_pointer):
            self.qscrs [i].acquire_screen (pscr)

        self.load ()

    def replace (self, keys):
        pass


    def __getitem__ (self, key):
        return getattr (self.qscr, key)

    def prev (self, p = None):
        self.unload ()

        if not p:
            p = self.qscr_pointer
            self.qscr_pointer -= 1

        else:
            self.qscr_pointer, p = p, self.qscr_pointer

        if self.qscr_pointer < 0:
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


    def next (self, p = None):
        self.unload ()

        if not p:
            p = self.qscr_pointer
            self.qscr_pointer += 1

        else:
            self.qscr_pointer, p = p, self.qscr_pointer

        if self.qscr_pointer >= self.qscr_len:
            self.qscr_pointer = 0

        if not self.qscrs [self.qscr_pointer].has_screen ():
            if self.qscrs [p].has_screen ():
                self.qscrs [self.qscr_pointer].acquire_screen (
                        *self.qscrs [p].release_screen ()
                        )
            else:
                self.qscr_pointer = p
                return -1

        self.load ()

    def __eq__ (self, value):
        return hasattr (self, 'qscr') and self.qscr == value

    def load (self, ps = None, scr = None):
        if ps:
            self.unload (ps)

        if scr == None:
            scr = self.qscrs [self.qscr_pointer]
        self.pscr = scr.pscr
        self.qscr = scr.qscr
        self.nav = scr.nav
        self.pscr.box ()
        self.pscr.refresh ()

        self.scrdim = (scr.scrdim [0] - 2, scr.scrdim [1] - 2)
        self.scord = (scr.scord [0] + 1, scr.scord [1] + 1)

        self.qline = scr.qline
        self.qmgr = scr.boot ()
        self.pqidx = scr.pqidx
        self.lpqidx = scr.lpqidx

        return self

    
    def unload (self, scr = None):
        if not scr:
            scr = self.qscrs [self.qscr_pointer]

        if hasattr (self, 'qline'):
            scr.qline = self.qline

        if hasattr (self, 'pqdix'):
            scr.pqidx = self.pqidx

        if hasattr (self, 'lpqidx'):
            scr.lpqidx = self.lpqidx

        scr.pscr.box (' ', ' ')
        scr.pscr.noutrefresh ()

        self.qscr = self.pscr = self.qmgr = self.nav = None

        self.scrdim = self.scord = None
        self.pqidx = self.lpqidx = -1
        self.qline = 0
        return self


    class Resizer:
        def __init__ (self, qscrs, pscrs, newlines, newcols, icall, cb = None):
            self.qscrs = qscrs
            self.newlines = newlines
            self.newcols = newcols
            self.pscrs = pscrs
            self.cb = cb
            self.icall = icall

        def __iter__ (self):
            yield from self.__next__ ()

        def __next__ (self):
            i = 0
            ps = None
            for scr in self.qscrs:
                scr.qscr.resize (self.newlines, self.newcols)

                if scr.has_screen ():
                    scr.release_screen ()
                    try:
                        s = self.pscr [i]
                        scr.acquire_screen (s)
                        yield self.icall (ps = ps, scr = scr)
                        ps = scr

                        i += 1

                    except IndexError:
                        pass

            
            if self.cb and hasattr (self.cb, '__call__'):
                self.cb ()

    def resize (self, pscreen):
        self.pscreen = pscreen

        scord, scrdim = self.pscreen.getbegyx (), self.pscreen.getmaxyx ()


        if scrdim [0] == 0:
            self.has_screen = False
            self.status_scr = None
            self.status_bar = None
            return -1
        
        else:
            self.has_screen = True
            d = 1
            if scrdim [0] == 1:
                self.qst_scr = self.pscreen
            else:
                if scrdim [0] > 2:
                    d = min (self.MAX_PHY_SCREENS, len (keys))

                self.status_scr = self.pscreen.derwin (1, scrdim [1], 0, 0)

                self.status_bar = curses.newpad (1, self.V_GRANULARITY)

                self.qst_scr = self.pscreen.derwin (scrdim [0] - 1, scrdim [1], 1, 0)
                scord, scrdim = self.qst_scr.getbegyx (), self.qst_scr.getmaxyx ()


        minlines = math.trunc ((scrdim [0]) / d)

        self.subscreens = []

        for i in range (d):
            self.subscreens.append (
                    self.qst_scr.derwin (minlines, scrdim [1], i * minlines, 0)
                    )

        i += 1

        self.subscreens [-1].resize (minlines + (scrdim [0] - (i * minlines) + 1), scrdim [1])

        self.vscreen.resize (self.V_GRANULARITY * len (self.qscr_len),
                scrdim [1] - 2)

    
        return self.Resizer (self.qscrs, self.subscreens, self.V_GRANULARITY,
                scrdim [1] - 2, self.load, self.load)



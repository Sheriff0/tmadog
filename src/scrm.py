import math
import copy
import pdb

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
    def __init__ (self, qscr, id = None, **kwargs):
        self.qscr = qscr
        self.id = id
        self.extras = kwargs

    def __getitem__ (self, key):
        if hasattr (self, key):
            return getattr (self, key)

        else:
            return self.extras [key]

    def __setitem__ (self, key, value):
        self.extras [key] = value

    def __contains__ (self, key):
        return key in self.extras

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

    def __init__ (self, pscreen, params):

        self.pscreen = pscreen

        scord, scrdim = self.pscreen.getbegyx (), self.pscreen.getmaxyx ()

        self.qst_scr = self.pscreen

        self.subscreens = []

        self.subscreens.append (
                Pscr (self.qst_scr)
                )


        qscrs = QScrList ()

        self.dimref = scrdim

        self.gparams = iter (params)
        self.params = params

        qscrs.append (
                QScr (
                    curses.newpad (self.V_GRANULARITY, self.dimref [1] - 1),
                    id = 0,
                    ** next (self.gparams)
                    )
                )


        self.qscrs = qscrs

        self.qscr_len = 1

        self.qscr_pointer = 0

        self.post_init ()


    def post_init (self):
        for i, pscr in enumerate (self.subscreens, self.qscr_pointer):
            self.qscrs [i].acquire_screen (pscr)

        self.load ()

    def replace (self, keys):
        pass

    def __getitem__ (self, key):
        return self.qscrs [self.qscr_pointer][key]

    def __setitem__ (self, key, value):
        self.qscrs [self.qscr_pointer] [key] = value

    def __contains__ (self, key):
        return key in self.qscrs [self.qscr_pointer]


    def scroll (self, offset):

        p = self.qscr_pointer

        if offset > 0 and (self.qscr_pointer + offset) >= self.qscr_len:
            for roff in range (offset):
                try:
                    self.qscrs.append (
                            QScr (
                                curses.newpad (self.V_GRANULARITY, self.dimref[1] - 1),
                                id = self.qscr_len + roff,
                                ** next (self.gparams)
                                )
                            )
                except StopIteration:
                    roff -= 1
                    break

            self.qscr_len += roff + 1

        self.qscr_pointer += offset

        if self.qscr_pointer < 0:
            self.qscr_pointer = self.qscr_len - 1
        elif self.qscr_pointer >= self.qscr_len:
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
        return self.qscr_pointer


    def load (self, scr = None):

        if scr == None:
            scr = self.qscrs [self.qscr_pointer]

        self.scrdim = (scr.scrdim [0], scr.scrdim [1] - 1)
        self.scord = (scr.scord [0] , scr.scord [1])

        return self


    def resize (self, pscreen):
        self.pscreen = pscreen

        self.pscreen.clear ()

        scord, scrdim = self.pscreen.getbegyx (), self.pscreen.getmaxyx ()


        self.qst_scr = self.pscreen

        self.subscreens = []

        self.subscreens.append (
                Pscr (self.qst_scr)
                )


        ptr = self.qscr_pointer

        i = 0
        idx = None

        for scr in self.qscrs:
            scr.qscr.resize (self.V_GRANULARITY, scrdim [1] - 1)

            if scr.has_screen ():
                scr.release_screen ()
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



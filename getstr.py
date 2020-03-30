import curses, curses.ascii

def pgetstr (pad, refresh_args, y = None, x = None, n = -1, chars = []):

    pdim = pad.getmaxyx ()
    
    chars = bytearray (chars)

    clen = len (chars)

    while True:
        c = pad.getch (y, x)

        if curses.ascii.isprint (c):

            cord = pad.getyx ()

            scord = cord [0] * pdim [1] + cord [1]

            if n >= 0 and clen == n:
                pass

            elif scord < clen:
                chars.insert (scord, c)
                pad.addstr (chars [scord:])
                pad.clrtoeol ()
                pad.move (*cord)
                pad.addch (chars [scord])

            else:
                pad.addch (c)
                chars.append (c)

            clen += 1
            

            if (cord [0] - refresh_args [0]) > (refresh_args [4] - refresh_args
                    [2]):
                refresh_args [0] += 1

        elif c == curses.KEY_BACKSPACE:
            pad.addch (c)

            cord = pad.getyx ()

            scord = cord [0] * pdim [1] + cord [1]
            
            pad.delch ()

            chars.pop (scord)

            if scord < clen:
                pad.addstr (bytes (chars [scord:]))
                pad.clrtoeol ()
                pad.move (*cord)

            clen -= 1
            

        elif c == curses.KEY_LEFT:
            cord = pad.getyx ()
            
            if cord [1] == 0:
                pad.move (cord [0] - 1, pdim [1] - 1)

            else:
                pad.move (cord [0], cord [1] - 1)


        elif c == curses.KEY_RIGHT:
            cord = pad.getyx ()
            
            if cord [1] < (pdim [1] - 1):
                pad.move (cord [0], pdim [1] + 1)

            else:
                pad.move (cord [0] + 1, 0)

        elif c == curses.KEY_UP or c == curses.KEY_DOWN:
            pass

        else:
            pad.refresh (*refresh_args)
            return (bytes (chars), c)

        pad.refresh (*refresh_args)

        if isinstance (n, int):
            n -= 1

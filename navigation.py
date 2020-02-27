import configparser
import dogs
import requests
import urllib.parse
import re
    
class InvalidPath (TypeError):
    def __init__ (self, *pargs, **kwargs):
        return super ().__init__ (*pargs, **kwargs)


class Recipe (object):
    def __init__ (self, steps, indices, keys, start, name):
        if not isinstance (start, requests.models.Response):
            raise TypeError ('Recipe: start must of type requests.models.Response', start)

        self.steps = steps.split (',')
        self.indices = indices.split (',')
        self.start = start
        self.keys = keys
        self.name = name
        self.len = len (self.steps)

    def __call__ (self, start):
        if start:
            if not isinstance (start, requests.models.Response):
                raise TypeError ('Recipe: start must of type requests.models.Response', start)

            else: 
                self.start = start

        return self

    def __repr__ (self):
        return '<Recipe for %s>' % (self.name,)

    def __iter__ (self):
        return self.__next__()

    def __next__ (self):
        
        for s,i in zip (self.steps, self.indices):
            s = s.strip ()
            if s.startswith (('[', '<')):
                data = {
                        k: self.keys[k] for k in s.split ('/')
                        }

                yield dogs.fill_form (
                        url = self.start.url,
                        idx = int (i),
                        html = self.start.text,
                        data = data,
                        flags = dogs.FILL_FLG_EXTRAS
                        )

            else:
                yield dogs.click (
                        url = self.start.url,
                        idx = int (i),
                        html = self.start.text,
                        button = s,
                        flags = dogs.FILL_FLG_EXTRAS
                        
                        )



class Navigation (object):

    class Navigator (object):
        def __init__ (self, home_url, webmap, keys, session = requests, **kwargs):
            self.webmap = webmap
            self.keys = keys
            self.cache = {}
            self.session = session 
            self.traverse_deps = True
            self.kwargs = kwargs
            self.kwargs.update (
                    headers = {
                        'host': urllib.parse.urlparse (home_url).hostname,
                        'referer': home_url,
                        'sec-fetch-mode': 'navigate',
                        'sec-fetch-user': '?1',
                        'sec-fetch-site': 'none'
                        }
                    )
            res = session.get (home_url, **self.kwargs)
            res.raise_for_status ()

            self.cache['home_page'] = res
            self.lp = 'home_page'

        def __repr__ (self):
            return self.cache[self.lp].url

        def __str__ (self):
            return self.cache[self.lp].text

        def __call__ (self, new_lp = None, **kwargs):
            self.lp = new_lp if new_lp else self.lp
            self.kwargs
            return self

        def __contains__ (self, value):
            return value in self.cache

        def __getitem__ (self, sl):
            if isinstance (sl, int):
                sl = slice (None, sl)
                s = self.lp 
            
            elif isinstance (sl, slice):
                s = self.lp 
            
            elif isinstance (sl, str):
                s = sl
                sl = slice (None, None)

            if s in self and ((s in self.webmap and not self.webmap.getboolean (s, 'volatile')) or
                    (re.match (r'\w+:-?\d', s))):
                return self.cache[s]
            
            elif s in self.webmap:
                if self.traverse_deps:
                    s1 = s
                    deps = []
                    while True:
                        s1 = self.webmap [s1]['requires']
                        if s1 in self and not self.webmap.getboolean (s1, 'volatile'):
                            break
                        else:
                            deps.append (s1)

                    while True:
                        if deps:
                            self.__goto__ (lp = deps.pop ())

                        else:
                            break

                return self.__goto__ (lp = s, sl = sl)

            else:
                raise Exception ('Location %s not in map' % (sl,))


        def __goto__ (self, lp = None, sl = slice (None, None)):
            lp = lp if lp else self.lp
            req_gen = Recipe (self.webmap [lp]['path'], self.webmap[lp]['indices'],
                    self.keys, self.cache[self.webmap [lp]['requires']], lp)

            gen = next (req_gen)

            res = None

            referer = self.cache[self.webmap [lp]['requires']].url

            for i, r in zip (range (req_gen.len)[sl], gen):


                self.kwargs.update (
                        headers = dogs.mkheader (r ['url'], referer)
                        )

                res = self.session.request (**r, **self.kwargs)

                res.raise_for_status ()
                referer = res.url

                req_gen (res)


            try:
                r = next (gen)
                k = lp + ':' + str (sl.stop)
                self.cache [k] = (
                        r,
                        res
                        )
                return self.cache [k]

            except StopIteration:
                self.cache [lp] = res
                self.lp = lp
                return res


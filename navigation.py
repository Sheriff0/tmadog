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
            self.home_url = home_url
            self.cache = {}
            self.session = session 
            self.traverse_deps = True
            self.kwargs = kwargs

        def __repr__ (self):
            return self.cache[self.lp].url

        def __str__ (self):
            return self.cache[self.lp].text

        def __call__ (self, new_lp = None, **kwargs):
            self.lp = new_lp if new_lp else self.lp
            self.kwargs.update (kwargs)
            return self

        def __contains__ (self, value):
            return value in self.cache

        def reconfigure (self, home_url, webmap = None, keys = None, session =
                None, **kwargs):
            self.webmap = webmap if webmap else self.webmap
            self.keys = keys if keys else self.keys
            self.session = session if session else self.session
            self.traverse_deps = True
            self.kwargs = kwargs if kwargs else self.kwargs

            if 'home_page' not in self or self ['home_page'].url != home_url:
                self.boot ('home_page')

        def __getitem__ (self, sl):
            if isinstance (sl, int):
                sl = slice (None, sl)
                s = self.lp 
            
            elif isinstance (sl, slice):
                s = self.lp 
            
            elif isinstance (sl, str):
                s = sl
                sl = slice (None, None)

            v = self.webmap.get (s, 'volatile', fallback = '')

            if s in self and ((not v or v not in self) or
                    (re.match (r'\w+:-?\d', s))):
                return self.cache[s]
            
            elif s in self.webmap:
                if self.traverse_deps:
                    deps = [s]
                    while True:
                        s1 = self.webmap [deps [-1]]['requires']
                        if not s1:
                            break

                        v = self.webmap [s1]['volatile']
                        if not v and s1 in self:
                            if urllib.parse.urlparse (self.cache [s1].url).hostname == urllib.parse.urlparse (self.cache ['home_page'].url).hostname:
                                break
                            else:
                                deps.append (s1)
                        
                        elif v and v not in self and s1 in self:
                            break

                        else:
                            deps.append (s1)
                    deps.reverse ()

                    for s1 in deps [:-1]:
                        self.__goto__ (lp = s1)
                        v = self.webmap [s1]['volatile']
                        if v and v in self:
                            self.cache.pop (v)



                v = self.webmap [deps [-1]]['volatile']
                if v and v in self:
                    self.cache.pop (v)

                return self.__goto__ (lp = deps [-1], sl = sl)

            else:
                raise Exception ('Location %s not in map' % (sl,))


        def __goto__ (self, lp = None, sl = slice (None, None)):


            lp = lp if lp else self.lp

            if not self.webmap [lp]['requires']:
                return self.boot (lp)

            x = self.cache [self.webmap [lp]['requires']]

            req_gen = Recipe (self.webmap [lp]['path'], self.webmap[lp]['indices'],
                    self.keys, x, lp)

            gen = next (req_gen)

            res = None

            referer = req_gen.start.url

            for i, r in zip (range (req_gen.len)[sl], gen):

                self.kwargs ['headers'].update (
                        dogs.mkheader (r ['url'], referer)
                        )

                res = self.session.request (**r, **self.kwargs)

                res.raise_for_status ()
                referer = res.url

                req_gen (res)


            try:
                r = next (gen)
                k = lp + ':' + str (sl.stop)
                if not res:
                    res = self.cache[self.webmap [lp]['requires']]

                self.cache [k] = (
                        r,
                        res
                        )
                return self.cache [k]

            except StopIteration:
                self.cache [lp] = res
                self.lp = lp
                return res
        
        def boot (self, page):

            self.kwargs.setdefault ('headers', {})

            self.kwargs ['headers'].update (
                    {
                        'host': urllib.parse.urlparse (self.home_url).hostname,
                        'referer': self.home_url,
                        'sec-fetch-mode': 'navigate',
                        'sec-fetch-user': '?1',
                        'sec-fetch-site': 'none'
                        }
                    )

            res = self.session.get (self.home_url, **self.kwargs)
            res.raise_for_status ()

            self.cache[page] = res
            self.lp = page

            return res


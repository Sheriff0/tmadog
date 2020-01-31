import configparser
import dogs
import requests

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



class Navigator (object):
    def __init__ (self, home_url, webmap, keys, session = requests):
        self.webmap = webmap
        self.keys = keys
        self.cache = {}
        self.session = session 
        res = session.get (home_url)
        self.cache['home'] = res
        self.lp = 'home'

    def __repr__ (self):
        return self.cache[self.lp].url

    def __str__ (self):
        return self.cache[self.lp].text

    def __call__ (self, new_lp = None):
        self.lp = new_lp if new_lp else self.lp
        return self

    def __getitem__ (self, sl):
        if isinstance (sl, int):
            sl = slice (None, sl)
        
        elif isinstance (sl, slice):
            pass
        
        elif isinstance (sl, str):
            if sl in self.cache:
                return self.cache[sl]
            
            else:
                return self.__goto__ (lp = sl)

        else:
            raise TypeError ('index must be "int" or "slice" or str')

        return self.__goto__ (sl = sl)

    def __goto__ (self, lp = None, sl = slice (None, None)):
        lp = lp if lp else self.lp
        req_gen = Recipe (webmap [lp]['path'], webmap[lp]['indices'],
                self.cache['home'], lp)

        gen = next (req_gen)

        for i, r in zip (range (req_gen.len)[sl], gen):
            res = self.session.request (*r)
            req_gen (res)

        try:
             return next (gen)

        except StopIteration:
            self.cache [lp] = res
            self.lp = lp
            return res


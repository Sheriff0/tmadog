import configparser
import libdogs
import requests
import urllib.parse
import re
import pdb

class InvalidPath (TypeError):
	def __init__ (self, *pargs, **kwargs):
		return super ().__init__ (*pargs, **kwargs)


class Recipe (object):
	def __init__ (self, steps, indices, keys, start, name_or_url):
		self (start)
		self.steps = steps.split (',')
		self.indices = indices.split (',')
		self.keys = keys
		self.name_or_url = name_or_url
		self.len = len (self.steps)

	def __call__ (self, start):
		if start:
			if not isinstance (start, requests.Response):
				raise TypeError ('Recipe: start must of type requests.models.Response', start)

			else:
				self.start = start
		else:
			self.start = requests.Response ()

		return self

	def __repr__ (self):
		return '<Recipe for %s>' % (self.name_or_url,)

	def __iter__ (self):
		yield from self.__next__()

	def __next__ (self):

		for s,i in zip (self.steps, self.indices):
			s = s.strip ()
			req = {}

			if s.startswith (('/', 'http')):
				a = s.split (':')

				req ['url'] = urllib.parse.urljoin (self.name_or_url, a [0])

				if len (a) > 1 and a [-1].strip ():

					req ['data'] = {
							k: self.keys[k] for k in a [-1].split ('/') if k in self.keys
							}
					req ['method'] = 'POST'

				else:
					req ['method'] = 'GET'

			elif self.start.url and self.start.text:
				if s.startswith (('[', '<')):
					data = {
							k: self.keys[k] for k in s.split ('/')
							}

					req.update (
							libdogs.fill_form (
								url = self.start.url,
								idx = int (i),
								html = self.start.text,
								data = data,
								flags = libdogs.FILL_FLG_EXTRAS
								)
							)
				else:
					req.update (
							libdogs.click (
								url = self.start.url,
								idx = int (i),
								html = self.start.text,
								button = s,
								flags = libdogs.FILL_FLG_EXTRAS

								)
							)

			else:
				raise TypeError ()

			yield req


class Navigator (object):
	def __init__ (self, home_url, webmap, keys, session = requests, **kwargs):
		self.webmap = webmap
		self.keys = keys
		self.home_url = home_url
		self.cache = {}
		self.session = session
		self.traverse_deps = True
		self.kwargs = kwargs
		self.refcount = 1
		self.kwargs.setdefault ('headers', {})

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
			self.cache.pop ('home_page', None)

	def __getitem__ (self, sla):
		if isinstance (sla, int):
			sl = slice (None, sla)
			s = self.lp

		elif isinstance (sla, slice):
			s = self.lp
			sl = sla

		elif isinstance (sla, str):
			s = sla
			sl = slice (None, None)

		v = self.webmap.get (s, 'volatile', fallback = '')

		if s in self and sl.stop == None and (not v or v not in self):
			return self.cache [s]

		elif (not v or v not in self) and '%s:%s' % (s, sl.stop) in self:
			return self.cache ['%s:%s' % (s, sl.stop)]

		elif s in self.webmap:
			if self.traverse_deps:
				deps = [s]

				if not self.webmap [s]['path'].startswith (('/', 'http')):
					while True:
						s1 = self.webmap [deps [-1]]['requires']

						if not s1:
							break

						elif self.webmap [s1]['path'].startswith (('/', 'http')):
							deps.append (s1)
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

		x = self.cache.get (self.webmap [lp]['requires'], None)

		req_gen = Recipe (self.webmap [lp]['path'], self.webmap[lp]['indices'],
				self.keys, x, self.home_url)

		gen = next (req_gen)

		res = None

		referer = req_gen.start.url

		for i, r in zip (range (req_gen.len)[sl], gen):

			self.kwargs ['headers'].update (
					libdogs.mkheader (r ['url'], referer)
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



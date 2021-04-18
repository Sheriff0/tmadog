import re
import pathlib
import email
import urllib
import requests


def parse_cook (fstr, targets):

    m = None

    headers = email.message.Message ()

    for m in re.finditer (r'(?<![-_])(set-cookie2?)[^-_]*?(?::|=|\n.*?[:=])\W*(' + '|'.join (targets) + r')( *=?[^"\'\n\\]+)', fstr, flags = re.I):

        headers [m.group (1)] = m.group (2) + m.group (3).strip ('"\' \n')


    return headers


def bake_cookies (
        f_or_str,
        url,
        targets = [r'.*?'],
	others = [],
        method = 'GET',
        ):

    def info ():
        nonlocal headers
        return headers

    class Response:
        def __init__ (self, attr, value):
            setattr (self, attr, value)

    url = urllib.parse.urlparse (url)

    headers = parse_cook (f_or_str, targets.copy ())

    if headers:
        for other in others:
            m = re.search (r'(?<![_-])(' + other + r'\b)[^-_]*?(?::|=|\n.*?[:|=])\W*([^"\'\n\\]+)', f_or_str, re.I)
            if m:
                headers [m.group (1)] = m.group (2)

        req = urllib.request.Request (url.geturl (), origin_req_host = url.hostname,
                method = method)


        cookies = requests.cookies.RequestsCookieJar()

        res = Response ('info', info)

        cookies.extract_cookies (res, req)

        return (headers, cookies)
    else:
        return None

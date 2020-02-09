import http.server
import pathlib
import sys
import argparse
import random
import math
from urllib import parse
import re

def nolog (*args):
    pass

class RequestHandler (http.server.BaseHTTPRequestHandler):

    _cookies = (x for x in range (20))

    def do_GET (self):
        self.log_req ()

        if self.path == '/':
            self.path = '/index.php'
        
        p = pathlib.Path (self.root + '/', self.path[1:])

        if p.exists ():
            self.send_response (200)
            self.send_header ('Content-Length', p.stat ().st_size)

            self.send_header ('Content-Type', 'text/html')

            self.end_headers ()

            self.wfile.write (p.read_bytes ()) 
        else:
            self.send_error (400)


    def do_POST (self):
        
        self.log_req ()
        
        if self.path.endswith (('stuser.php', 'tmuser.php')):
            self.login ()

    def login (self):
            
        p = pathlib.Path (self.root + '/', self.path[1:] + '.post')
        
        if p.exists ():

            if not hasattr (self, 'active_st'):
                self.active_st = {}

            cookie = self.headers.get ('cookie', None) or str (next (self._cookies))
            if not hasattr (self, 'data'):
                self.data = self.rfile.read (int (self.headers.get ('content-length', 0))).decode ()
        
            if not self.data:
                raise Exception ('login: no data provided')

            d = dict (
                    map (
                        lambda a: (a.split ('=')[0], parse.unquote_plus (a.split ('=')[-1])), 
                        self.data.split ('&')
                        )
                    )
            

            self.active_st [cookie] = d['matno'] 
            s = p.read_text ()

            s = re.sub (r'nou\d{9}', d ['matno'].upper (), s, flags = re.I)

            self.send_response (200)

            self.send_header ('Content-Type', 'text/html')

            self.send_header ('Set-Cookie', cookie + '; path=/')

            self.end_headers ()

            self.active_st.setdefault (cookie, d['matno'])

            self.wfile.write (bytes (s, encoding = 'utf8')) 

        else:
            self.send_error (400)


    def log_req (self):
        print ('''url: %s
method: %s
headers: %a''' % (self.path, self.command, dict (self.headers)))
        
        self.data = self.rfile.read (int (self.headers.get ('content-length', 0))).decode ()

        if self.data:
            print ('data:', self.data)

    class MessageClass (http.server.BaseHTTPRequestHandler.MessageClass):

        def __iter__ (self):
            
            for t in zip (self.keys, self.values):
                yield t

        def __next__ (self):
            return self.__iter__ ()



def main (argv = sys.argv):

    parser = argparse.ArgumentParser ()
    parser.add_argument ('--silent', action = 'store_true', help = 'No logs whatsoever')

    parser.add_argument ('--dir', default = '.', help = 'Directory from which to service requests')
    
    parser.add_argument ('--host', default = 'localhost', type = str,
            help = 'The hostname for the server')
    
    parser.add_argument ('--port', default = 3000, type = int, help = 'The port for the server')
    
    parser.add_argument ('--no-run', dest = 'run', action = 'store_false', help = 'Run the server')


    args,ukn = parser.parse_known_args (argv or [])

    RequestHandler.root = args.dir

    if args.silent:
        RequestHandler.log_request = nolog
        RequestHandler.log_message = nolog
        RequestHandler.log_error = nolog
        RequestHandler.log_req = nolog
    
    server = http.server.HTTPServer ((args.host, args.port), RequestHandler)
   
    if not args.silent and args.run:
        print ('root set to %s' % (RequestHandler.root,))
        print ('Server to listen on port %d' % (args.port,))
    
    try:
        return (
                server,
                ukn or []
                ) if not args.run else server.serve_forever ()

    except KeyboardInterrupt:
        server.shutdown ()

if __name__ == '__main__':
    main ()

import http.server
import pathlib
import sys
import argparse

class RequestHandler (http.server.BaseHTTPRequestHandler):


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
        self.do_GET ()
        print ('data:', self.rfile.read ().decode ())

    def log_req (self):
        print ('''url: %s
method: %s
headers: %a''' % (self.path, self.command, dict (self.headers)))

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
    
    if not args.silent:
        print ('root set to %s' % (RequestHandler.root,))
    
    server = http.server.HTTPServer ((args.host, args.port), RequestHandler)
   
    if not args.silent:
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

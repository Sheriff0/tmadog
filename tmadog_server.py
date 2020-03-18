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


qtemplate ='''<html>
<body>
<form method="post" action="qsak3_ynz.php" onsubmit="return confirm('Are you sure you want to submit this answer?');"><!--    <center>  <button type="button" class="btn btn-default" onclick="randomizeList()">Show Question</button></center>-->

  <ol>
<p style="text-align: right"><input type="submit" name ="esubmit"  class="btn btn-info" value="Submit"></p>

      <li class="dropdown" value = "{qj:d}">{matno}:{qdescr}<hr>      							<a href="#" class="dropdown-toggle btn btn-default" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false" onclick="randomizeList()">Show Options</a>

    <ul class="dropdown-menu" id="tmopt">
      <li>{matno} <input type='radio' name="ans" value="A">{opta}</li>
        <li>{matno} <input type='radio' name="ans" value="B">{optb}</li>
          <li>{matno} <input type='radio'name="ans" value="C">{optc}</li>
            <li>{matno} <input type='radio' name="ans" value="D">{optd}</li></ul> </li>
      
    
<input type="hidden" name="qid" value="{qid}"/>
<input type="hidden" name="qdescr" value="{qdescr}"/>

<input type="hidden" name="opta" value="{opta}"/>
<input type="hidden" name="optb" value="{optb}"/>
<input type="hidden" name="optc" value="{optc}"/>
<input type="hidden" name="optd" value="{optd}"/>
<input type="hidden" name="ku3si" value="{crscode}{matno}TMA{tma}"/>
<input type="hidden" name="rumbu" value="tqadva"/>
<input type="hidden" name="xstore" value="trexdva"/>
      <input type="hidden" name="tmastid" value="{matno}"/>

</ol>
 
<input type="hidden" name="tmano" value="TMA{tma}"/>
<input type="hidden" name="qj" value="{qj:d}"/>
<input type="hidden" name="crscode" value="{crscode}"/>
<input type="hidden" name="totscore" value="{totscore:d}"/>
<!--<p style="text-align: right"><input type="submit" name ="esubmit"  class="btn btn-info" value="Submit"></p>-->
</form>
</body>
</html>'''

atemplate = '''<html>
<body>
You have scored {mark:d} mark for question. Your total score is {totscore:d} out of 10
</body>
</html>'''

class RequestHandler (http.server.BaseHTTPRequestHandler):

    _cookies = (x for x in range (100))

    active_st = {}

    qsts = [
	    { 'qdescr': 'Adjudication is made up of the following components except ________.', 'opta': 'Internal accessor', 'crscode': 'PCR811', 'qid': '15079', 'ans': 'A', 'optb': 'Law court', 'optc': 'Lawyer', 'optd': 'Magistrate' },

	    {'qdescr': 'The two types of arbitration are _______ and voluntary.', 'opta': 'Compulsory', 'crscode': 'PCR811', 'qid': '15080', 'ans': 'A', 'optb': 'Competitive', 'optc': 'Private', 'optd': 'distributive arbitration'}, 

	    {'qdescr': 'Conflict management according to Wilmot and Hocker begins from', 'opta': 'Remaining rational', 'crscode': 'PCR811', 'qid': '15086', 'ans': 'D', 'optb': 'Negotiation', 'optc': 'Mediation', 'optd': 'Communication and perception'},

	    {'qdescr': 'The process whereby trans-border transactions are increasingly shrinking the entire universe into a relatively borderless sphere is referred to as _______', 'opta': 'Treaties', 'crscode': 'PCR811', 'qid': '15082', 'ans': 'D', 'optb': 'Commonwealth of nations', 'optc': 'Africa and European Unions', 'optd': 'Globalization'},

	    {'qdescr': 'Which of the following is not among the wide range of mediation activities?', 'opta': 'message carrying', 'crscode': 'PCR811', 'qid': '15083', 'ans': 'D', 'optb': 'fact finding', 'optc': 'good officers', 'optd': 'host-taking strategy'},

	    {'qdescr': 'The judicial approach is essentially a settlement of dispute by _______', 'opta': 'conciliation', 'crscode': 'PCR811', 'qid': '15078', 'ans': 'B', 'optb': 'Litigation', 'optc': 'Mediation', 'optd': 'confrontation'},

	    {'qdescr': '_________ comprises certain post-conflict activities in a back-and forth relationship, namely disarmament, demilitarization and reintegration', 'opta': 'enforcement', 'crscode': 'PCR811', 'qid': '15081', 'ans': 'B', 'optb': 'Peacebuilding', 'optc': 'coersion', 'optd': 'Rearmament'},

	    {'qdescr': 'Which of the following is an instant messaging application ? (a) WhatsApp (b) Google Talk (c) Viber Select the correct Ans: from the codes given below :', 'opta': '(a) and (b) only', 'crscode': 'CIT701', 'qid': '63895', 'ans': 'D', 'optb': '(b) and (c) only', 'optc': '(a) only', 'optd': '(a), (b) and ( c )'},

    {'qdescr': 'Which of the following is not involved in covert tactics?', 'opta': 'Back-channel contacts', 'crscode': 'PCR811', 'qid': '15085', 'ans': 'D', 'optb': 'Explore problem solving', 'optc': 'Secret venues', 'optd': 'Formal meeting'},

	    {'qdescr': 'A procedure that explains how IT professionals should describe user needs and develop applications to meet those needs is called', 'opta': 'operation procedure', 'crscode': 'CIT701', 'qid': '63240', 'ans': 'C', 'optb': 'back up procedure', 'optc': 'development procedure', 'optd': 'security procedure'},

	    {'qdescr': 'A temporary storage area in the processor that can move data and instructions more quickly than main memory can, and momentarily hold the data or instructions used in processing as well as the results that are generated is', 'opta': 'hard drive', 'crscode': 'CIT701', 'qid': '63244', 'ans': 'B', 'optb': 'register', 'optc': 'memory', 'optd': 'flip-flop'},

	    {'qdescr': 'Which of the following elements is not considered in determining processor speed', 'opta': 'system clock', 'crscode': 'CIT701', 'qid': '63248', 'ans': 'D', 'optb': 'bus width', 'optc': 'word size', 'optd': 'flip-flop'},

	    {'qdescr': 'Information technology professional who works with users to determine the requirements an application must meet is', 'opta': 'programmer', 'crscode': 'CIT701', 'qid': '63246', 'ans': 'B', 'optb': 'system analyst', 'optc': 'system designer', 'optd': 'web designer'},

	    {'qdescr': 'One trillionth of a second is', 'opta': 'millisecond', 'crscode': 'CIT701', 'qid': '63249', 'ans': 'D', 'optb': 'microsecond', 'optc': 'nanosecond', 'optd': 'picoseconds'},

	    {'qdescr': 'Which of the following signs is not a logical operation', 'opta': '||', 'crscode': 'CIT701', 'qid': '63243', 'ans': 'A', 'optb': '<', 'optc': '=', 'optd': '/'},

	    {'qdescr': 'A circuit that generates electronic impulses at a fixed rate to synchronize processing activities is called', 'opta': 'System Clock', 'crscode': 'CIT701', 'qid': '63245', 'ans': 'A', 'optb': 'Bus Width', 'optc': 'Word Size', 'optd': 'Memory'},

	    {'qdescr': 'An IT procedure that describes how and when to make extra copies of information or software to protect against losses is known as', 'opta': 'operation procedure', 'crscode': 'CIT701', 'qid': '63247', 'ans': 'B', 'optb': 'back up procedure', 'optc': 'security procedure', 'optd': 'development procedure'},

	    {'qdescr': 'Which of the following components is not part of processor', 'opta': 'transistor', 'crscode': 'CIT701', 'qid': '63242', 'ans': 'D', 'optb': 'integrated circuit', 'optc': 'control unit', 'optd': 'power unit'}, 
	    ]

    def do_GET (self):
        self.log_req ()

        status = 200

        if self.path == '/':
            if self.cfmode:
                self.path = '/cf.html'
                status = 503
            else:
                self.path = '/index.html'

        elif self.path.startswith ('/?__cf_chl_jschl_tk__'):
            self.path = '/index.php'

        elif self.path == '/stuserout.php':
            try:
                self.active_st.pop (self.headers.get ('cookie').split ('=')[-1])
                self.path = '/stuser.php'
            except:
                self.send_error (400)
                return

        
        p = pathlib.Path (self.root + '/', self.path[1:])

        if p.exists ():
            self.send_response (status)

            self.send_header ('Content-Length', p.stat ().st_size)

            self.send_header ('Content-Type', 'text/html')

            self.end_headers ()

            self.wfile.write (p.read_bytes ()) 
        else:
            self.send_error (400)


    def do_POST (self):
        
        
        if self.path.endswith (('stuser.php', 'tmuser.php')):
            self.log_req ()
            self.login ()
        
        elif self.path.endswith ('dzaden3_ynd.php'):
            self.log_req ()
            self.getqst ()

        elif self.path.endswith ('qsak3_ynz.php'):
            self.log_req ()
            self.getans ()

        elif self.path.startswith ('/?__cf_chl_jschl_tk__'):
            self.do_GET ()

    
    def getans (self):

        m, s = self.active_st.get (self.headers.get ('cookie', 'xx').split ('=')[-1], (None, None))
        if not hasattr (self, 'data'):
            self.data = self.rfile.read (int (self.headers.get ('content-length', 0))).decode ()

        if not m or not self.data:
            self.send_error (400)
            return

        d = self.parse_data (self.data)
        for q in self.qsts:
            if q ['qid'] == d ['qid']:

                self.send_response (200)
                self.send_header ('Content-Type', 'text/html')
                self.end_headers ()

                mark = 1 if q ['ans'] == d ['ans'] else 0

                s [d ['crscode']]['totscore'] = int (s [d ['crscode']]['totscore']) + mark

                s [d ['crscode']]['qj'] = int (s [d ['crscode']]['qj']) + 1

                self.active_st [self.headers ['cookies']] = (m, s)

                self.wfile.write (bytes (atemplate.format (totscore = s [d ['crscode']]['totscore'], mark = mark), encoding = 'utf8'))
                return

        self.send_error (400)
        return

    def getqst (self):

        m, s = self.active_st.get (self.headers.get ('cookie', 'xx').split ('=')[-1], (None, None))
        if not hasattr (self, 'data'):
            self.data = self.rfile.read (int (self.headers.get ('content-length', 0))).decode ()

        if not m or not self.data:
            self.send_error (400)
            return

        d = self.parse_data (self.data)
        g = re.findall (r'([a-zA-Z]{3}\d{3}).+TMA([1-3])', d ['krs3id'], flags = re.I)[0]

        qst = random.choice (self.qsts).copy ()
        s.setdefault (g[0], {})
        s [g[0]].update (qst)

        s [g[0]].setdefault ('qj', 1)
        s [g[0]].setdefault ('totscore', 0)
        s [g[0]]['crscode'] = g[0]
        s [g[0]]['tma'] = g[1]
        s [g[0]]['matno'] = m
            
        self.send_response (200)

        self.send_header ('Content-Type', 'text/html')

        self.end_headers ()

        self.wfile.write (bytes (qtemplate.format (**s [g[0]]), encoding = 'utf8')) 

        return

    def parse_data (self, data):
        return dict (
                map (
                    lambda a: (parse.unquote_plus (a.split ('=')[0]), parse.unquote_plus (a.split ('=')[-1])), 
                    data.split ('&')
                    )
                )
            

    def login (self):
            
        p = pathlib.Path (self.root + '/', self.path[1:] + '.post')
        
        if p.exists ():

            if not hasattr (self, 'active_st'):
                self.active_st = {}

            cookie = self.headers.get ('cookie').split ('=')[-1] if 'cookie' in self.headers else str (next (self._cookies))
            if not hasattr (self, 'data'):
                self.data = self.rfile.read (int (self.headers.get ('content-length', 0))).decode ()
        
            if not self.data:
                self.send_error (400)
                return

            d = self.parse_data (self.data) 
            s = p.read_text ()

            s = re.sub (r'nou\d{9}', d ['matno'].upper (), s, flags = re.I)

            self.send_response (200)

            self.send_header ('Content-Type', 'text/html')

            if cookie not in self.active_st:
                self.send_header ('Set-Cookie', 'id=' + cookie + '; path=/')

            self.end_headers ()

            self.active_st.setdefault (cookie, (d['matno'], {}))

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

    parser.add_argument ('--cfmode', action = 'store_true', help = 'To use cfmode')
    
    parser.add_argument ('--no-run', dest = 'run', action = 'store_false', help = 'Run the server')


    args,ukn = parser.parse_known_args (argv or [])

    RequestHandler.root = args.dir
    RequestHandler.cfmode = args.cfmode

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

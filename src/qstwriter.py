import json
import pathlib

#A custom copy of NOUN question page header
header = """<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>

<title>{crscode}</title>

<style>
* {box-sizing:border-box}
body {font-family: Verdana,sans-serif;}
.mySlides {display:none}

/* Slideshow container */
.slideshow-container {
  max-width: 400px;
  padding: 22px 22px;
  position: relative;
  margin: auto;
}

/* Caption text */
.text {
  color: #f2f2f2;
  font-size: 15px;
  padding: 8px 12px;
  position: absolute;
  bottom: 8px;
  width: 100%;
  text-align: center;
}

/* Number text (1/3 etc) */
.numbertext {
  color: #f2f2f2;
  font-size: 12px;
  padding: 8px 12px;
  position: absolute;
  top: 0;
}

/* The dots/bullets/indicators */
.dot {
  height: 15px;
  width: 15px;
  margin: 0 2px;
  background-color: #bbb;
  border-radius: 50%;
  display: inline-block;
  transition: background-color 0.6s ease;
}

.active {
  background-color: #717171;
}

/* Fading animation */
.fade {
  -webkit-animation-name: fade;
  -webkit-animation-duration: 5.5s;
  animation-name: fade;
  animation-duration: 5.5s;
}

@-webkit-keyframes fade {
  from {opacity: .4}
  to {opacity: 1}
}

@keyframes fade {
  from {opacity: .4}
  to {opacity: 1}
}

/* On smaller screens, decrease text size */
@media only screen and (max-width: 300px) {
  .text {font-size: 11px}
}
</style>


<center>
<h3> <strong><p class="text-success">{crscode}</p></strong> </h3></p>
</center>

 <style>
    li {
    font-size: 85%;
    padding: 0px 5px;
}


a:link {
    color: red;
}

a:visited {
    color: green;
}

a:hover {
    color: hotpink;
}

a:active {
    color: blue;
}

</style>
</head>
        """;

body="""
<body>
<ol>

<li class="dropdown" value = "1">{qn}. {qst} <hr>

<ul class="dropdown-menu" id="tmopt">
  <li><input type='checkbox' checked> {ans} </li>
</ul>
</li>
  
</ol>

        """;

trailer = """
</body>
</html>""";


class QstWriter:
    def __init__(self, qlist, qmap, outfunc = None):
        self.qmap = qmap;
        self.qlist = list(qlist);
        self.outfunc = outfunc;
    
    def __repr__(self):
        st = "";
        for crs, qpage in self:
            line = "%s" % ("=" * len(crs),);
            st += "%s\n%s\n%s\n\n" % (line,crs,line);
            for q,a in qpage:
                st += "%s\n\t%s\n\n" % (q,a);
        
        return st;
    
    def __str__(self):
        return repr(self);

    def __iter__(self):
        slist = [];
        lqlist = self.qlist.copy()
        while True:
            if not lqlist:
                self.qlist = slist;
                break
            crscode = lqlist[0][self.qmap["crscode"]];
            
            pcount = 0;
            qpage = [];
            for pi, q in enumerate(lqlist.copy()):
                if q[self.qmap["crscode"]]  != crscode:
                    continue;
                qpage.append(
                        (
                            q[self.qmap["qdescr"]],
                            q[self.qmap["ans"]],
                            )
                        );
                slist.append(lqlist.pop(pi - pcount));
                pcount += 1;

            yield [crscode, qpage];


    def write(self):
        if self.outfunc and callable(self.outfunc):
            return self.outfunc(self);
        else:
            return print(self);


def fromJSONf(f, qmap, outfunc = None):
    fp = pathlib.Path(f);
    if fp.exist():
        fstr = fp.read();
        return fromJSONs(fstr, qmap, outfunc);
    else:
        return "";

def fromJSONs(qstr, qmap, outfunc = None):
    qsts = json.loads(qstr);
    if not isinstance(qsts, list):
        return "";
    else:
        return fromlist(qsts, qmap, outfunc)


def fromlist(qsts, qmap, outfunc = None):
    return QstWriter(qsts, qmap, outfunc).write();

def writetxt(outpat = "{c}.txt"):
    def write(qiter):
        for crs, qpage in qiter:
            st = "";
            line = "%s" % ("=" * len(crs),);
            st += "%s\n%s\n%s\n\n" % (line,crs,line);
            qn = 1;
            for q,a in qpage:
                if a:
                    st += "%s. %s\n\t-->%s\n\n" % (qn,q,a);
                    qn+=1;

            with open(outpat.format(c = crs), "a") as fp:
                fp.write(st);

    return write;

def writehtml(outpat = "{c}.html"):
    def write(qiter):
        for crs, qpage in qiter:
            st = "";
            line = "%s" % ("=" * len(crs),);
            st += "%s\n%s\n%s\n\n" % (line,crs,line);
            qn = 1;
            for q,a in qpage:
                st += "%s. %s\n\t-->%s\n\n" % (qn,q,a);
                qn+=1;

            with open(outpat.format(c = crs), "a") as fp:
                fp.write(st);

    return write;

def writeqst(outpat = "{c}.txt"):
    if outpat.endswith((".txt", ".TXT")):
        return writetxt(outpat);
    elif outpat.endswith((".html", ".HTMl")):
        return writehtml(outpat);
    else:
        return writetxt(outpat);

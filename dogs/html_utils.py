import requests
import re

def uncomment_html (html):
    return re.sub (r'<!--.+?-->?', '\n', html, flags = re.MULTILINE | re.DOTALL)


def gethtml_tag (nodestr):
    m = re.search (r'<\s*(?P<tag>\b\w+\b).+?<\s*/\s*(?P=tag)\s*>', nodestr, re.MULTILINE | re.DOTALL)
    if m:
        return m.group ('tag')
    else:
        return None


def subnomatch (text, post, *rest):
    
    def cb (mobj):
             alt_pat, m = mobj
             if not m:
                m = re.search (alt_pat, text, *rest)
                if not m:
                    return None
             if m:
                return eval ('m.%s' % (post))

    return cb


def txtnode_to_name_attr (html, targ):
    
    if isinstance (targ, str):
        m = re.search (r'<\s*.+?name\s*=\s*(\'|")(?P<name>[^\'"]*)\1.*?>\s*'+ targ + r'\s*<\s*/.+?>' , html, re.MULTILINE)
        if m:
            return m.group ('name')
        else:
            return None
    elif isinstance (targ, list):
       return list (map (subnomatch (html, 'group("name")', re.MULTILINE), 
               [ (r'<\s*.+?name\s*=\s*(\'|")(?P<name>' + t + r')\1.*?>', re.search (r'<\s*.+?name\s*=\s*(\'|")(?P<name>[^\'"]*)\1.*?>\s*'+ t +
           r'\s*<\s*/.+?>', html, re.MULTILINE)) for t in targ ])) 



def txtnode_to_value_attr (html, targ):
    if isinstance (targ, str):
        m = re.search (r'<\s*.+?value\s*=\s*(\'|")(?P<value>[^\'"]*)\1.*?>\s*'+ targ
                + r'\s*<\s*/.+?>', html,
        re.MULTILINE)

        if not m:
            m = re.search (r'<\s*.+?value\s*=\s*(\'|")(?P<value>' + targ +
                    r')\1.*?>', html, re.MULTILINE)

        if m:
            return m.group ('value')
        else:
            return None
    elif isinstance (targ, list):
       return list (map (subnomatch (html, 'group("value")', re.MULTILINE), 
               [ (r'<\s*.+?value\s*=\s*(\'|")(?P<value>' + t + r')\1.*?>', re.search (r'<\s*.+?value\s*=\s*(\'|")(?P<value>[^\'"]*)\1.*?>\s*'+ t +
           r'\s*<\s*/.+?>', html, re.MULTILINE)) for t in targ ])) 



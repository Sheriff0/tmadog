def login (url, ldata):
    index = tmadogsess.get (url, headers = {'referer': url})

    index.raise_for_status()
    
    lpage = click (index.text, 'Take TMA3', url+'xxx', idx = 0, headers = {
        'referer': url,
        }, 
        session = tmadogsess)

    lpage.raise_for_status()

    propage = fill_form (lpage.text, lpage.request.url , NO_TXTNODE_VALUE |
            NO_TXTNODE_KEY, idx = 0, nonstdtags = ['button'],
            headers = {
                'referer': lpage.url,
                'origin': url[0:-1],
                'cache-control': 'max-age=0'
                }, data = ldata, session = tmadogsess)
    
    propage.raise_for_status()
    
    return propage


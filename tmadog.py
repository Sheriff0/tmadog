import sys
import cfscrape
import os
from dogs import *
import utils

tmadogsess = cfscrape.create_scraper ()

defhdr = {
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-site': 'same-origin'
        }

tmadogsess.headers.update (defhdr)


# -*- coding: utf-8 -*-
"""
@author: Cat Chenal
@module: gc4settings.py
"""
__author__ = 'catchenal@gmail.com'

import os
from dotenv import load_dotenv, find_dotenv


# globals, paths:
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#print('BASE_DIR', BASE_DIR)

# data folder:
DIR_GEO = os.path.join(BASE_DIR, 'geodata') 
#print('DIR_GEO', DIR_GEO)
DIR_SHP = os.path.join(DIR_GEO, 'shapefiles')

DIR_HTML = os.path.join(DIR_GEO, 'html_frames')
#print('DIR_HTML', DIR_HTML)
DIR_CSS = DIR_HTML

DIR_IMG = os.path.join(BASE_DIR, 'images')
#print('DIR_IMG', DIR_IMG)

# report folder:
DIR_RPT = os.path.join(BASE_DIR, 'report') 

NB_CSS = 'style.min.css'

# globals, locations used for the comparison:
#  Putting the variables that will be used to compose the geo query string into their own lists,
#  makes it clear that they are of the same type & easier to amend.

# query strings for places: the extended name for the 2nd one is intentional (to get the monument)
lst_places = ["New York City", "Cleopatra's needle, Central Park, New York", "Boston"]
# state id of above places:
lst_ST = ['NY', 'NY', 'MA']
# NYC counties:
lst_counties = ['Bronx', 'Kings', 'New York', 'Queens', 'Richmond']

query_lst = ["New York City, NY, USA",
             "Cleopatra's needle, Central Park, New York, NY, USA",
             "Bronx county, NY, USA",
             "Kings county, NY, USA",
             "New York county, NY, USA",
             "Queens county, NY, USA",
             "Richmond county, NY, USA",
             "Boston, MA, USA"]

# globals, geocoders:
geocs = ['Nominatim', 'GoogleV3', 'ArcGis', 'AzureMaps']
colors_dict = dict(zip(geocs, ['red', 'green', 'darkblue', 'cyan']))


def load_env():
    """
    Find .env automacically by walking up directories until it's found
    """
    d_env_path = find_dotenv()
    
    if (d_env_path is None) or (len(d_env_path)== 0):
        msg = "Local '.env' file not found.\n \
        The Socrata credential variables are set to None, which may not be accepted.\n \
        If that's the case, create the file with the credentials as KEY=value on each line.\n \
        Google Maps/Places is also loaded (temp)."
        print(msg)
        return None
    else:
        # load up the entries as environment variables
        load_dotenv(dotenv_path=d_env_path, verbose=True)
        

# globals, account keys:
local_data_found = load_env()

GOOGLE_KEY = os.getenv("GOO_GEO_API_1")
AZURE_KEY = os.getenv("AZ_KEY_1")
W3W_dict = {w:os.getenv(w) for w in ['W3W_USER','W3W_PWD','W3W_NAME','W3W_API']}


def copy_nb_css():
    import notebook
    import shutil

    src = os.path.join(notebook.DEFAULT_STATIC_FILES_PATH, 'style', NB_CSS)
    
    css_path = os.path.join(DIR_HTML, NB_CSS)
    if not os.path.exists(os.path.join(css_path)):
        shutil.copy(src, DIR_HTML)
    
    tpl_path = os.path.join(DIR_HTML, 'templates', NB_CSS)
    if not os.path.exists(os.path.join(tpl_path)):
        shutil.copy(src, os.path.join(DIR_HTML, 'templates'))
    
    return

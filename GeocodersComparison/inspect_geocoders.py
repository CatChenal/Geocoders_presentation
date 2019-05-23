# -*- coding: utf-8 -*-
"""
@author: Cat Chenal
@module: comparison.py
"""
__author__ = 'catchenal@gmail.com'

import os

import inspect
import geopy
import pandas as pd

from IPython.display import HTML, Markdown, Image, IFrame

from GeocodersComparison import gc4settings
from GeocodersComparison import gc4utils


def as_of():
    import datetime
    return datetime.datetime.today().strftime("%b %Y")


def get_dict_geocs_class():
    """Create a dict of geopy.geocoders: name, class."""
    geopy_geocs_d = {}

    for k, v in geopy.geocoders.SERVICE_TO_GEOCODER.items():
        # keep only google:
        if k == 'googlev3':
            continue
        # exclude Pelias (Linux Foundation):
        #   geocoder server api to download?
        if k == 'pelias':
            continue

        geopy_geocs_d[k] = v
        
    return geopy_geocs_d


def get_dict_geocs_required_params(geocs_dict):
    """
    Return a dictionnary of required parameter for each
    geocoders in geocs_dict.
    :param: geocs_dict: output of get_dict_geocs_class().
    """
    
    geopy_geocs_reqs = {}
    
    for name, obj in geocs_dict.items():

        sig = inspect.signature(obj)

        # note: all param.kind == POSITIONAL_OR_KEYWORD, 
        # this is a workaround to get positional args:
        positional = "<class 'inspect._empty'>"

        required = []
        for param in sig.parameters.values():
            tup = (param.name,  str(param.default))

            # Known exceptions as per initial error testing:
            #
            # Google: UserWarning: Since July 2018 Google requires each request to have an API key. 
            #        Pass a valid `api_key` to GoogleV3 geocoder to hide this warning. 
            #        See https://developers.google.com/maps/documentation/geocoding/usage-and-billing
            # Nominatim:  DeprecationWarning: Using Nominatim with the default "geopy/1.19.0" `user_agent` 
            #       is strongly discouraged, as it violates Nominatim's ToS 
            #       https://operations.osmfoundation.org/policies/nominatim/ and may possibly cause
            #       403 and 429 HTTP errors. Please specify a custom `user_agent` with 
            #       `Nominatim(user_agent="my-application")` or by overriding the default `user_agent`: 
            #  ---> `geopy.geocoders.options.default_user_agent = "my-application"`.
            #       In geopy 2.0 this will become an exception.      
            # geonames: No username given, required for api access.  If you do not have a GeoNames username, 
            #       sign up here: http://www.geonames.org/login
            # openmapquest:  OpenMapQuest requires an API key
            #
            if name == 'google':
                if tup[0] == 'api_key':
                    tup = ('api_key', positional)
            if name == 'geonames':
                if tup[0] == 'username':
                    tup = ('username', positional)
            if name == 'openmapquest':
                if tup[0] == 'api_key':
                    tup = ('api_key', positional)

            if tup[1] == positional:
                required.append(tup[0])

        if required:
            geopy_geocs_reqs[name] = required
            
    return geopy_geocs_reqs


def check_new_requirements(geocs_dict, geocs_reqs_dict):
    """
    Check actual outcome when geocoding: 
    if errors & not expected from inspection info obtained via
    get_dict_geocs_required_params(), then indicate that
    further exceptions need defining (as with Google).
    """
    # set user_agent & timeout defaults for all geocoders:
    geopy.geocoders.options.default_user_agent = 'this_app/1'
    geopy.geocoders.options.default_timeout = 5

    import warnings

    init_errors = {}

    with warnings.catch_warnings():
        warnings.simplefilter("error")

        for name, obj in geocs_dict.items():
            try:
                g = obj()
                del g

            except (DeprecationWarning,
                    UserWarning,
                    TypeError,
                    geopy.exc.GeopyError) as e:

                s = str(e)
                if s.startswith('__'):
                    skip = len('__init__() missing ')
                    s = s[skip:]
                    i = s.index(': ')
                    s = s[i+2:].replace("'", '').replace('and', '').split()

                init_errors[name] = s

            continue

    msg = ''
    for k_err in init_errors.keys():
        # compare with the information obtain from the
        # inspection of the class parameters:

        k_reqs = geocs_reqs_dict.get(k_err)
        if k_reqs is None:
            msg = __name__ + ': Mismatch found viz class definition ({}).\n'.format(as_of())
            msg += 'Some geocoder may need a new exception in get_dict_geocs_required_params().\n'
            msg += '   New error raise for {}\n'.format(k_err)
            print(msg)        
    return msg


def inspect_geopy_geocs(geocs_dict, geocs_reqs_dict):
    
    geocs_tot = len(geocs_dict.keys())
    geocs_with_reqs = len(geocs_reqs_dict.keys())

    s  = 'Number of Geopy geocoders (minus Pelias): {};\n'.format(geocs_tot)
    s += '...... {} ({:.0%}) of them '.format(geocs_with_reqs, 
                                              geocs_with_reqs/geocs_tot)
    s += 'have API requirements as of {}.\n'.format(as_of())

    msg_new_reqs = check_new_requirements(geocs_dict, geocs_reqs_dict)
    
    return s + msg_new_reqs


def get_geocs_reqs_df(geocs_dict, geocs_reqs_dict, load_from_dict=True):
    """
    If load_from_dict=True, and json file of the data dict is found, 
    a pd dataframe is created from the dict, if not:
    Combine geocoders name, class and reqs into a pd dataframe.
    Save its data dict as 'src/report/geocs_class_reqs.json';
    Return the dataframe and its data dict.
    """
    fname = os.path.join(gc4settings.DIR_RPT, 'geocs_class_reqs.json')
    
    if load_from_dict:
        if os.path.exists(fname):
            df = pd.read_json(fname).sort_index()

        else:
            load_from_dict = False
        
    if not load_from_dict:   
        data = {}
        for k, v in geocs_dict.items():
            classname = str(v)[7:-1]
            r = geocs_reqs_dict.get(k)
            data[k] = [classname, r]

        df = pd.DataFrame.from_dict(data, orient='index').reset_index()
        df.columns = ['Geocoder','Class','Requires']
        
        df['Comments'] = ''
        txt = "Search restricted to the continental, European territory "
        txt += "of France; limit=1 does not seem to work."
        df.loc[df.Geocoder=='banfrance', 'Comments'] = txt
        txt = "The Open Street Map (OSM) geocoder: fast & free!"
        df.loc[df.Geocoder=='nominatim', 'Comments'] = txt
        df.loc[df.Geocoder=='yandex', 'Comments'] = "Returns most json values in Russian."

    # save data dict in json file
    dd = df.to_dict()
    gc4utils.save_df_dict(fname, dd)

    return df, dd


def geocoders_hilighted(df, caption=''):
    
    def hilight_col1(row):
        ret = ["" for _ in row.index]
        if row.Requires is None:
            ret[row.index.get_loc('Geocoder')] = "background-color: palegreen"
        return ret

    tbl_styles = [dict(selector="th", props=[('background-color', '#f7f7f9'),
                                             ("text-align", "center"),
                                             ("font-size", "150%")
                                            ]),
                  dict(selector="td", props=[("font-size", "120%")]),
                  dict(selector="caption", 
                       props=[("caption-side", "top"),
                             ("font-size", "160%"),
                             ("font-weight", "bold")])
                 ]

    df = (df.style
            .apply(hilight_col1, axis=1)
            .set_table_styles(tbl_styles)
            .set_caption(caption)
            .hide_index()     
         )
    return df


def save_inspect_report(df, n_geocs, n_geocs_reqs):
    """
    Create and save HTML report in GeocodersComparison/report folder as 
    geocs_inspect.html.
    Parameter: output of get_geocs_reqs_df(geopy_geocs, geopy_geocs_reqs).
    Returns the filepath which can be used as follows in jupyter:
    ```html_rpt = save_inspect_report(df, n_geocs, n_geoc_reqs)
        IPython.display.HTML(filename=html_rpt)
    ```
    """
    nomin_note = "Note: Nominatim has no requirement as long as "
    nomin_note += "the user_agent is not Geopy's (geopy/n.n.n).<br>"
    nomin_note += "The user_agent can be set globally with, e.g.: geopy."
    nomin_note += "geocoders.options.default_user_agent='my-app/version'"
    nomin_note += "."
    
    msg = ''
    msg += """<h3> As of {}, Geopy wraps {} geocoders and {}
    of them have an API requirement:</h3>{}""".format(as_of(),
                                                         n_geocs,
                                                         n_geocs_reqs,
                                                         nomin_note)
    cap = 'Geocoding APIs available via Geopy.geocoders; Highlights identify free access.'
    html_df = geocoders_hilighted(df, caption=cap).render()

    tpl = """
    <!DOCTYPE html>
    <head>    
        <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
        <link rel="stylesheet" 
         href="https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap.min.css"/>
        <link rel="stylesheet" 
         href="https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap-theme.min.css"/>
        <link rel="stylesheet" 
         href="https://maxcdn.bootstrapcdn.com/font-awesome/4.6.3/css/font-awesome.min.css"/>

    </head>
    <body>
        <div> <small>{}</small> </div>
        <br>
        <div> <table>{}</table> </div>
    </body>
    """.format(msg, html_df)

    tplname = os.path.join(gc4settings.DIR_RPT, "geocs_inspect.html")
    gc4utils.save_file(tplname, 'html', tpl, replace=True)
    
    return tplname


def show_w3w_endpoints():
    ul = """<h3 style="text-align:left;"><ul>
    <li> word.word.word &rarr; coordinate <span style="color:red;">&raquo;</span> 
    https://api.what3words.com/v2/forward?addr=[3 words]&key=[ ]<br></li>
    <li> coordinates &rarr; word.word.word <span style="color:red;">&raquo;</span> 
    https://api.what3words.com/v2/reverse?coords=[lat,lon]&key=[ ]<br></li>
    <li> bbox &rarr; grid <span style="color:red;">&raquo;</span> 
    https://api.what3words.com/v2/grid?bbox=[box NE SW bounds]&format=json&key=[ ]<br></li>
    </ul></h3>"""
    return HTML(ul)
 
 
def show_w3w_nyc_results():
    ul = """<h4 style="text-align:left;"><ul>
    <il>"Manhattan, New York, NY USA" &rarr; "soil.pushes.mole"
          <br>&nbsp;&nbsp;&nbsp;:: a square within the Met museum</li>
    <li>"New York county, NY, USA" &rarr; "dress.sharp.brave
        <br>&nbsp;&nbsp;&nbsp;:: City Hall</li>
    <li>"Brooklyn, NY, USA" &rarr; "recent.pints.giving"
        <br>&nbsp;&nbsp;&nbsp;:: Intersection of Atlantic & Brooklyn aves</li>
    <li>"Kings county, NY, USA" &rarr; "recent.pints.giving"
        <br>&nbsp;&nbsp;&nbsp;:: same</li>
    </ul></h4>"""
    return HTML(ul)
    
    
def show_geoc_access():
    ul = """<h3 style="text-align:left;"><ul>
    <li>directly in a browser address box</li>
    <li>via the `requests` library</li>
    <li>with a wrapping library such as <a href="https://geopy.readthedocs.io/en/stable/">Geopy</a></li>
    </ul></h3>"""
    return HTML(ul)


def show_map_components():
    dir_html = gc4settings.DIR_HTML
    
    fname_boston_rel = os.path.relpath(os.path.join(dir_html, 'Boston.html'))
    #return HTML("""<h1>What's in a map?</h1>
    return HTML("""<div float="top" width="100%">
          <iframe src="{}" width="700" height="400" frameborder="0"></iframe>
          <iframe srcdoc="<br><ul>
                        <li><h2>a mapping software</h2></li>
                        <li><h2>a shapefile</h2></li>
                        <li><h2>data: point locations</h2></li>
                        <li><h2>data: bounding boxes</h2></li></ul>" 
             height="400" frameborder="0"></iframe>
         </div>""".format(fname_boston_rel))


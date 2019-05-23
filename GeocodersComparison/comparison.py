# -*- coding: utf-8 -*-
"""
@author: Cat Chenal
@module: comparison.py
"""
__author__ = 'catchenal@gmail.com'

import os
import itertools
from collections import OrderedDict

from GeocodersComparison import gc4settings
from GeocodersComparison import gc4utils

import numpy as np
import pandas as pd
import geopandas as gpd

from geopy import distance as geod
from geopy.geocoders import Nominatim
from geopy.geocoders import GoogleV3
from geopy.geocoders import ArcGIS
from geopy.geocoders import AzureMaps # no longer works; acessing the API w/requests

import folium
import matplotlib.pyplot as plt

from IPython.display import display
# =============================================================================


def get_geodata(geocoder_to_use, query_list, use_local=True, alt_prefix=''):
    """
    Wrapper function for using one of four geocoders: 'Nominatim', 'GoogleV3',
    'ArcGis', 'AzureMaps', to retrieve the geographical data of places in
    query_list.

    Parameters
    ----------
    :param: geocoder_to_use (str): to switch geocoding service
    :param: query_list (list): a list of cities, places or counties
    :param: use_local (bool), default=True: a local file returned if found
    :param: alt_prefix (str), default='': to retrieve a geojson file tagged
            with that prefix => use_local=True (old file).

    Returns
    -------
    geodata (odict): odict_keys(['loc', 'box']) where
              loc=['lat', 'lon'] and box=[[NE lat, lon], [SW lat, lon]].
    Note: the loc key identifies the place queried, not the entire string.

    Example
    -------
    >>> geo_Nom = get_geodata('Nominatim', ['New York City, NY, USA'])

    >>> geo_Nom['New York City'].keys()
    odict_keys(['loc', 'box'])
    """

    # init checks:
    if geocoder_to_use not in geocs:
        msg = 'Function setup for these geocoders: {}, not for: {}'
        msg = msg.format(geocs, geocoder_to_use)
        raise Exception(msg)

    if (not isinstance(query_list, list)):
        msg = '"query_list" must be a list. Given is: {}'
        msg = msg.format(type(query_list))
        return TypeError(msg)

    # to check for & save local file; base name w/o extension:
    out = 'geodata_' + geocoder_to_use[:3]
    
    no_fetching = len(alt_prefix)
    if no_fetching:
        # implied: pre-existing file: no overwriting.
        use_local=True
        if alt_prefix[-1] != '_':
            out = alt_prefix + '_' + out
        else:
            out = alt_prefix +  out
        

    if use_local:
        geodata = gc4utils.get_geo_file(os.path.join(gc4settings.DIR_GEO,
                                                     out + '.json'))
        
        if not geodata is None:
            return geodata
        else:
            if no_fetching:
                print("Non overwritable file not found:\t{}".format(out))
                return None
            else:
                # Fetch it
                use_local = False

    if not use_local:

        tout = 5
        idx = geocs.index(geocoder_to_use)

        if idx == 0:
            g = Nominatim(user_agent='this_app', country_bias='USA',
                          timeout=tout)
        elif idx == 1:
            g = GoogleV3(api_key=GOOGLE_KEY, timeout=tout)
        elif idx == 2:
            g = ArcGIS(user_agent='this_app', timeout=tout)
        else:
            # original setup stopped working 9/12/18: unable to resolve the
            # http 400 error; reverted to request/json.
            g = AzureMaps(subscription_key=AZURE_KEY,
                          user_agent='ths_app', timeout=tout)
            #url_Azure = 'https://atlas.microsoft.com/search/address/json'

        geodata = OrderedDict()

        for i, q in enumerate(query_list):
            info_d = OrderedDict()

            # build the key=place for the output dict, w.r.t. county or not:
            if 'county' in q:
                place = q.split(' county, ')[0] + ' county'
            else:
                place = q.split(', ')[0]

            if idx == 0:
                location = g.geocode(q, addressdetails=True).raw  #exactly_one=False, 
            else:
                location = g.geocode(q).raw
                
            if isinstance(location, list):
                location = location[0]

            if len(location):   # not sure that's a sufficient check...
                
                if idx == 0:
                    # pt location
                    info_d['loc'] = [float(location['lat']),
                                     float(location['lon'])]
                    # bounding boxes as 2 corner pts: [NE], [SW]
                    info_d['box'] = [[float(location['boundingbox'][1]),
                                      float(location['boundingbox'][3])],
                                     [float(location['boundingbox'][0]),
                                      float(location['boundingbox'][2])]]

                elif idx == 1:
                    info_d['loc'] = [location['geometry']['location']['lat'],
                                     location['geometry']['location']['lng']]
                    info_d['box'] = [[location['geometry']['viewport']['northeast']['lat'],
                                      location['geometry']['viewport']['northeast']['lng']],
                                     [location['geometry']['viewport']['southwest']['lat'],
                                      location['geometry']['viewport']['southwest']['lng']]]

                elif idx == 2:
                    info_d['loc'] = [location['location']['y'],
                                     location['location']['x']]
                    info_d['box'] = [[location['extent']['ymax'],
                                      location['extent']['xmax']],
                                     [location['extent']['ymin'],
                                      location['extent']['xmin']]]

                else:
                    info_d['loc'] = [location['position']['lat'],
                                     location['position']['lon']]
                    info_d['box'] = [[location['viewport']['topLeftPoint']['lat'],
                                      location['viewport']['btmRightPoint']['lon']],
                                     [location['viewport']['btmRightPoint']['lat'],
                                      location['viewport']['topLeftPoint']['lon']] ]

            geodata[place] = info_d

        # save file (overwrite=default)
        outfile = os.path.join(DIR_GEO, out)
        gc4utils.save_file(outfile, 'json', geodata)

        return geodata


def get_pairwise_names(geocs):
    pair_comps = []
    for comp in itertools.combinations(geocs, 2):
        pair_comps.append('{} v. {}'.format(comp[0], comp[1]))

    return pair_comps


def compare_geocoords(geo_df, dist_units=['km', 'mi']):
    """
    To obtain a pairwise comparison of the geodata from exactly 4 geocoders.
    Parameters
    ----------
    :param geo_df (pandas.DataFrame): Holds the lat, lon, NE and SW data to be
    compared. DataFrame as formatted by :function:get_geodata_df().
    :param dist_units (list) : kilometers (km), miles (mi) or both.
    Returns
    ----------
    df (pandas.DataFrame): Values are the geodesic distance of the pairwise
    differences.
    """
    # input check:
    msg = __name__
    if geo_df.shape[0] != 4:
        msg += ': Expecting 4 rows of geolocation data.\n'
        msg += 'Given: {}'.format(geo_df.shape[0])
        raise Exception(msg)

    len_units = len(dist_units)
    if len_units > 2:
        msg += ': Expecting at most two units of distance, "km" and "mi".'
        msg += 'Given: {}'.format(dist_units)
        raise Exception(msg)

    both_units = (len_units == 2)
    if not both_units:
        if (len_units == 0):
            units = 'km'
        else:
            units = dist_units[0]

    pairwise_comps = get_pairwise_names(geo_df.index.tolist())
    name = geo_df.index.name

    comps_data = dict()

    # point location differences:
    i = 0
    # Found out about geopy.distance.util.pairwise, but I would still need
    # the iteration to populate comps_data, so I did not use it.
    for comp in itertools.combinations(geo_df[['lat, lon']].values, 2):
        d = geod.distance(comp[0], comp[1])

        if both_units:
            comps_data[pairwise_comps[i]] = {'Location_(km)': np.round(d.km, 6),
                                             'Location_(mi)': np.round(d.mi, 6)}
        elif (units=='km'):
            comps_data[pairwise_comps[i]] = {'Location (km)': np.round(d.km, 6)}
        else:
            comps_data[pairwise_comps[i]] = {'Location (mi)': np.round(d.mi, 6)}
        i += 1

    # box corners differences:
    i = 0
    for comp in itertools.combinations(geo_df[['NE', 'SW']].values, 2):
        NE_d = geod.distance(comp[0][0], comp[1][0])
        SW_d = geod.distance(comp[0][1], comp[1][1])

        if both_units:
            comps_data[pairwise_comps[i]].update(
                                               {'NE_(km)': np.round(NE_d.km, 6),
                                                'NE_(mi)': np.round(NE_d.mi, 6),
                                                'SW_(km)': np.round(SW_d.km, 6),
                                                'SW_(mi)': np.round(SW_d.mi, 6)}
                                               )
        elif (units=='km'):
            comps_data[pairwise_comps[i]].update(
                                               {'NE (km)': np.round(NE_d.km, 6),
                                                'SW (km)': np.round(SW_d.km, 6)}
                                               )
        else:
            comps_data[pairwise_comps[i]].update(
                                               {'NE (mi)': np.round(NE_d.mi, 6),
                                                'SW (mi)': np.round(SW_d.mi, 6)}
                                               )
        i += 1

    df = pd.DataFrame(comps_data).T
    df.index.set_names(name, inplace=True)
    if both_units:
        df.columns = df.columns.str.split('_', expand=True)

    return df


def get_geodata_df(geocs, geo_dict, place):
    data = [[gd[place]['loc'],
             gd[place]['box'][0],
             gd[place]['box'][1]] for _, gd in enumerate(geo_dict)]
    df = pd.DataFrame(data, index=geocs, columns=['lat, lon', 'NE', 'SW'])
    df.index.set_names(place, inplace=True)

    return df


def compare_two_geoboxes(place1, place2, geocs, geo_dict):
    """
    Return a pandas.DataFrame with the np.allclose() results for the bounding
    boxes of place1 and place2 for each geocoder.

    Usage
    -----
    To answer the question: "How does each geocoder treat the bounding boxes of
    these two locations, identically?". This is a quantitative check usefull to
    run when two boxes visualized on a map appear to have the same coordinates.

    Parameters
    ----------
    :param place1, place2 (str): Places to compare.
    :param geocs (list): Geocoders names.
    :param geo_dicts (list): Geocoding data dictionaries.

    Return
    ------
    df (pandas.DataFrame): Geocoder name, bool(Identical box?)
    """
    data = {}
    for i, g in enumerate(geo_dict):
        data[geocs[i]] = np.allclose(g[place1]['box'], g[place2]['box'])

    df = pd.DataFrame(pd.Series(data), columns=['Identical_bounding boxes?'])
    col0 = '{} & {}:'.format(place1, place2)
    df.columns = df.columns.str.split('_', expand=True)
    df.index.name = col0

    return df


def compare_location_with_geobox(places, geocs, geo_dicts, show_values=False):
    """
    Usage
    -----
    To answer the question: "Are a place's coordinates identical to those
    of the center of its bounding box?" for all geocoders in the comparison.
    Note: the earth is flat here, no geodesic distance.
    Return
    ------
    Pandas DataFrame
    """
    df_lst = []

    for i, g in enumerate(geo_dicts):
        geo = geocs[i]
        data_p = OrderedDict()

        for p, v in g.items():
            # p: places, v: geoms
            box_ctr = [(v['box'][0][0] + v['box'][1][0])/2,
                       (v['box'][0][1] + v['box'][1][1])/2]
            boo = np.allclose(np.round(v['loc'], 6),
                              np.round(box_ctr, 6),
                              atol=1e-06)

            if show_values:
                data_p[p] = {geo+'_location': np.round(v['loc'], 6),
                             geo+'_box center': np.round(box_ctr, 6),
                             geo+'_same?': boo}
            else:
                data_p[p] = {geo: boo}

        df_lst.append(pd.DataFrame(data_p).T)

    df = pd.concat(df_lst, axis=1, sort=False)

    if show_values:
        df.columns = df.columns.str.split('_', expand=True)
    else:
        df.index = places

    df.index.name = 'Location is box center?'

    return df


# Dataframe styling functions:
# These are not applied by the function that creates the df
# because the final object would be of type "Styler" and no longer open to
# DataFrame operations.
#
def highlight_max(s):
    is_max = s == s.max()
    return ['background-color: lightpink' if v else '' for v in is_max]


def highlight_min(s):
    is_min = s == s.min()
    return ['background-color: palegreen' if v else '' for v in is_min]


def center_hdr(df):
    # also centers the index column???
    align_hdr = [dict(selector="th", props=[('text-align', 'center'),
                                            ('background-color', '#f7f7f9')])]
    df = df.style.set_table_styles(align_hdr)
    return df


def with_style(df):
    cap = ('Four geocoders coordinates pairwise difference comparison<br>' +
           'with highlighted min (green) and max (pink) in each column.')

    styles = [dict(selector="th", props=[('background-color', '#f7f7f9'),
                                         ("text-align", "center")]),
              dict(selector="caption", props=[("caption-side", "bottom")])
              ]
    df = df.style.set_table_styles(styles)\
                 .apply(highlight_min)\
                 .apply(highlight_max)\
                 .format("{:.6f}")\
                 .set_caption(cap)
    return df


def get_geo_dicts(geocs, query_lst, use_local=True, alt_prefix=''):
    """
    For use in get_df_dict(geocs, geo_dicts, places) to obtain
    the respective dataframes for mapping.
    """
    if use_local:
        print('\nLoading geodata...')
    else:
        print('\nFetching geodata...')
    geo_Nom = get_geodata(geocs[0], query_lst,
                          use_local=use_local, alt_prefix=alt_prefix)
    geo_Goo = get_geodata(geocs[1], query_lst,
                          use_local=use_local, alt_prefix=alt_prefix)
    geo_Arc = get_geodata(geocs[2], query_lst,
                          use_local=use_local, alt_prefix=alt_prefix)
    geo_Azu = get_geodata(geocs[3], query_lst,
                          use_local=use_local, alt_prefix=alt_prefix)

    geo_dicts = [geo_Nom, geo_Goo, geo_Arc, geo_Azu]
    if any(d is None for d in geo_dicts):
        print('\nAlternate geodata not found.\n')
        return None
    else:
        print('\nAll geodata variables gathered into list geo_dicts.\n')
        return geo_dicts


def get_places(geo_dicts):
    """
    The dict places is used for retrieving the geodata '
    and the distance comparison for a particular place.'
    """
    places = list(geo_dicts[0].keys())
    places_to_boros = OrderedDict()
    places_to_boros[places[0]] = 'Manhattan'
    places_to_boros[places[1]] = 'Manhattan'
    places_to_boros[places[2]] = 'Bronx'
    places_to_boros[places[3]] = 'Brooklyn'
    places_to_boros[places[4]] = 'Manhattan'
    places_to_boros[places[5]] = 'Queens'
    places_to_boros[places[6]] = 'Staten Island'
    return places, places_to_boros


def get_df_dict(geocs, geo_dicts, places):
    """
    To obtain a dict of each place's data as a tuple (geodata_df, dist_diff_df)
    as per get_geodata_df() and compare_geocoords() outputs, respectively.
    """
    df_dict = OrderedDict()

    for p in places:
        # geocoder results:
        df1 = get_geodata_df(geocs, geo_dicts, p)
        # Distance differences:
        df2 = compare_geocoords(df1)
        
        df_dict[p] = (df1, df2)

    return df_dict


def get_geo_dist_heatmap(places, df_dict, unit='km',
                         save_fig=True, fig_frmt='svg'):
    """To show the pairwise geodistance comparison in 3 heatmaps for
       Lcation, NE corner, SW corner.
    """
    import seaborn as sns

    sns.set_context("notebook", font_scale=1., rc={"lines.linewidth": 1.})

    dist_frames_d = {}

    for p in places:
        # The pairwise distance daf is the second value;
        # Its string index is, e.g. 'Nominatim v. GoogleV3'
        dist_frames_d[p] = df_dict[p][1]

    combined_df = pd.DataFrame()

    for k, df in dist_frames_d.items():
        drop_unit = '(mi)'
        if unit == 'mi':
            drop_unit = '(km)'

        new = df.T.unstack(level=0).drop(drop_unit, axis=0)
        new.columns.set_names(['geocoders', 'geom'], inplace=True)
        new.index = [k]
        combined_df = pd.concat([combined_df, new])

    combined_df = combined_df.T
    combined_df.reset_index(inplace=True)

    # for sorting by geom location, NE, SW
    combined_df['sort_geo'] = ([g.split('v. ')[1]
                               for g in combined_df['geocoders']])

    combined_df.sort_values(by=['geom', 'sort_geo'], inplace=True)
    combined_df.set_index(combined_df.geocoders + '|' + combined_df.geom,
                          inplace=True)

    names = combined_df.geocoders.unique()

    combined_df.drop(['geocoders', 'geom', 'sort_geo'], axis=1, inplace=True)

    # Split into 3 to show corresponding heatmaps:
    locs_df = combined_df.loc[combined_df.index.str.endswith('Location')]
    NE_df = combined_df.loc[combined_df.index.str.endswith('NE')]
    SW_df = combined_df.loc[combined_df.index.str.endswith('SW')]

    # Plot heamap with seaborn:
    fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(18, 8), sharey=True)

    dfs = {0: locs_df, 1: NE_df, 2: SW_df}
    which_type = {0: 'Location', 1: 'NE corner', 2: 'SW corner'}

    # To center the color map:
    my_max_acceptable_difference = 5  # in km
    
    if unit == 'mi':
        my_max_acceptable_difference = my_max_acceptable_difference * 0.62

    for i, a in enumerate(ax):

        df = dfs[i]

        sns.heatmap(df, ax=a,
                    annot=True, fmt=".2f",
                    linewidths=0.5,
                    cmap='coolwarm',
                    center=my_max_acceptable_difference,
                    square=True,
                    cbar=False)

        a.set_xticklabels(a.get_xticklabels(),rotation=60)
        a.set_yticklabels(names, fontweight='bold', fontsize=12)
        a.set_title('{}\n'.format(which_type[i]),
                    fontweight='bold', fontsize=14)
        a.set_ylabel('')
        if i == 1:
            a.annotate(s='Geodesic distance difference ({}):'.format(unit),
                       xy=[0.5, 1.2], xycoords='axes fraction',
                       ha="center", fontweight='bold', fontsize=14)

    fig.tight_layout()

    # if not save, show:
    if save_fig:
        out = os.path.join(gc4settings.DIR_IMG,
                           'Heatmap_sns_geodist_difference_'
                           + unit + '.' + fig_frmt)
        plt.savefig(out, format=fig_frmt,
                    orientation='landscape', bbox_inches='tight')
    else:
        plt.show()

    return


def get_map(geo, zoom=14, map_style='cartodbpositron'):
    g = np.array(geo)
    mean_lat = g[..., 0].mean()
    mean_lon = g[..., 1].mean()

    m = folium.Map([mean_lat, mean_lon], 
                   tiles=map_style, 
                   zoom_start=zoom,
                   control_scale=True)
    return m


def add_box_and_markers(mapobj, gdf, colors_d, lc_loc = 'topright'):
    """
    Add location markers and a feature group, which provides an "interactive
    legend".
    """    
        
    place = r'{}'.format(gdf.index.name.replace("'", "\\'"))  # for apostrophes

    for i, row in gdf.iterrows():
        # i is a string index
        c = colors_d[i]
        if i == 'AzureMaps': c = '#00e6e6' # darker shade onlist
            
        grp1_name = '<span style=\\"color:' + c + ';\\">' + i + ' place'
        grp1_name += '</span>'
        grp1 = folium.FeatureGroup(grp1_name)

        tip = "{}, {}: {}".format(i, place, row['lat, lon'])

        folium.CircleMarker([row['lat, lon'][0], row['lat, lon'][1]],
                            radius=8,
                            color='black',
                            weight=0.8,
                            fill=True,
                            fill_color=colors_d[i],
                            fill_opacity=0.3,
                            tooltip=tip
                           ).add_to(grp1)
        grp1.add_to(mapobj)

        # boxes from geocoders:
        grp2_name = '<span style=\\"color:' + c + ';\\">' + i + ' box'
        grp2_name += '</span>'
        grp2 = folium.FeatureGroup(grp2_name)

        p1 = row.NE
        p3 = row.SW
        p2 = [p3[0], p1[1]]  # SE
        p4 = [p1[0], p3[1]]  # NW

        # 4 lines to a box:
        sides = [[p1, p2], [p2, p3], [p3, p4], [p4, p1]]
        folium.PolyLine(sides, color=colors_d[i]).add_to(grp2)
        grp2.add_to(mapobj)
        
    folium.map.LayerControl(lc_loc, collapsed=False).add_to(mapobj)

    return mapobj


def get_boro_maps(boro_name,
                  locs_df,
                  bounds_gdf,
                  filter_bounds=True,
                  colors_d={},
                  zoom=10,
                  map_style='cartodbpositron',
                  file_suffix=''):
    """
    To obtain a map with location markers, bounding box and bounds from
    shapefiles.
    Parameters:
    -----------
    :param boro_name: to filter dataframe 'bounds_gdf' [todo: error check].
    :type: str
    :param locs_df: Aggregated geocoding results for each place queried.
    :type: pandas.DataFrame
    :param bounds_gdf: Holds the shapfile data (bounds).
    :type: geopandas.DataFrame
    :param filter_bounds (default: True): Flag to proceed with the filtering of
           bounds_df with boro_name.
           If False, all the bounds will be rendered on the map, as with e.g.
           "New York City", or with another location where borough names do not
           appear in the shapefile, e.g. "Boston".
    :type: bool
    :param colors_d: Dict for each geocoder's color for folium elements.
    :param zoom: Starting zoom level (int).
    :param map_style (str): Default folium Tile.
    """
    def style_bounds(feature):
        return {'fillOpacity': 0.2,
                'weight': 1,
                'fillColor': '#eea700',
                'color': '#404040'}

    # Use one of the best geocoder to center the map
    m = get_map(locs_df.loc['Nominatim', ['lat, lon']].tolist(),
                    zoom=zoom, map_style=map_style)

    # show the shapefile data
    if filter_bounds:
        # in case bounds_gdf covers multiple locations
        gdf_boro = bounds_gdf[bounds_gdf.BoroName == boro_name]
        shp = folium.GeoJson(gdf_boro,
                       style_function=style_bounds,
                       name='shapefile bounds'
                       ).add_to(m)
    else: 
        shp = folium.GeoJson(bounds_gdf,
                       style_function=style_bounds,
                       name='shapefile bounds'
                       ).add_to(m)
    
    # Show boxes from shapefile:
    grp0_name = '<span style=\\"color:#404040;\\"> shapefile box'
    grp0_name += '</span>'
    grp0 = folium.FeatureGroup(grp0_name)
    
    lmin, lmax = shp.get_bounds()
    # [[lat_min, lon_min], [lat_max, lon_max]]

    p1 = lmax # NE
    p3 = lmin # SW
    p2 = [p3[0], p1[1]]  # SE
    p4 = [p1[0], p3[1]]  # NW

    # 4 lines to a box:
    sides = [[p1, p2], [p2, p3], [p3, p4], [p4, p1]]
    folium.PolyLine(sides, color='darkgrey').add_to(grp0)
    grp0.add_to(m)
    
    if not colors_d:        # empty:
        colors_d = dict(zip(locs_df.index.tolist(),
                            ['red','green','darkblue','cyan']))

    add_box_and_markers(m, locs_df, colors_d)

    # Save map:
    name = 'map'
    if not (locs_df.index.name is None):
        name = locs_df.index.name.replace(' ', '_')
    if file_suffix:
        name += '_' + file_suffix + '.html'
    else:
        name += '.html'

    m.save(os.path.join(gc4settings.DIR_HTML, name))

    return m


def get_gdf_boston():
    """
    To obtain a geo dataframe from shapefile with same format as NYC.
    # Boston: https://data.boston.gov/dataset/city-of-boston-boundary
    """
    from collections import OrderedDict
    
    gdf_boston = gpd.read_file(os.path.join(DIR_SHP, 'Boston.shp'),
                               driver='shapefile')

    gdf_boston.drop(['OBJECTID', 'BOSTON_LAN',], axis=1, inplace=True)

    newcols = OrderedDict()
    newcols['CITY'] = 'BoroCode'
    newcols['COUNTY'] = 'BoroName'
    newcols['SHAPEarea'] = 'Shape_Area'
    newcols['SHAPElen'] = 'Shape_Leng'

    gdf_boston.rename(mapper=newcols, axis=1, inplace=True)
    gdf_boston['BoroCode'] = 1
    gdf_boston['BoroName'] = 'Boston'
    
    return gdf_boston


def save_df_table_to_html(df, df_title, table_name_without_ext):
    from pandas.io.formats.style import Styler

    if isinstance(df, Styler):
        #styling already applied: keep
        ds = df.render()
        
        T = '<h5>{}</h5>\n '.format(df_title)
        style_tag = '<style  type="text/css" >\n'
        # add the title before style_tag:
        ds = ds.replace(style_tag, T + style_tag)
    else:
        tpl_path = os.path.join(gc4settings.DIR_HTML, 'templates')
        dfstyle = Styler.from_custom_template(tpl_path, "myhtml.tpl")
        ds = dfstyle(df).render(table_title=df_title)
        
    gc4utils.save_file(table_name_without_ext, 'html', ds)


def output_tables_3(places, df_dict):
    caption = 'Coordinates differences for location and box corners'
    tbl_list = []
    
    for i, p in enumerate(places):
        diff_df = df_dict[p][1]
        
        df_title = "Table 3.{}: {} [{}]".format(i+1, caption, p)
        name =  p.replace(' ','_')
        table = os.path.join(gc4settings.DIR_HTML, 
                             name + '_dist_diff.html')

        ds = with_style(diff_df)
        save_df_table_to_html(ds, df_title, table)
        tbl_list.append(table)
        
    return tbl_list


def df_to_pic(df,
              ax=None,
              new_col_names=[],
              header_columns=0,
              row_height=0.6,
              font_size=11,
              squeeze_factor=7.,
              header_color='#ecf7f9',
              row_colors=['#f1f1f2', 'w'],
              save_tbl_name='',
              show=False,
              fig_format='svg',
              bbox=[0, 0, 1, 1],
              **kwargs):
    """
    TODO:
    change default empty list to None + add check:
    if new_col_names is None:
         new_col_names = []

    Adapted from SO #39358752.
    To output a matplotlib.pyplot table from a pandas.DataFrame.
    Parameters:
    -----------
    :param df: pandas datarfame
    :param new_col_names: replaces the columns in case df has MultiIndex; list
    :param header_columns: Count of column to be bolded
    :param row_height: Height of each row
    :param font_size: Table cells font_size
    :param squeeze_factor: Enable the conversion from len('column names') to figure width in inches,
                           or to fine tune the display
    :params edge_color, header_color='w': Color strings
    :param row_colors: List of colors for alternating color scheme
    :param save_tbl_name: If given, the figure is saved with that name in geodata/images
    :param show: Bool flag to display output; should be True, if ax is an existing subplots axis [not tested]
    :param fig_format: Image format
    :params bbox, **kwargs: Argument passed to plt table for futher styling

    """
    import six          # iteritems

    col_pad = 0.05

    #if len(df.columns) == 1:
    #    df = df.reset_index()
        
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [' '.join(col).strip() for col in df.columns.values]
        
    df = df.reset_index()
    
    if 'index' in df.columns:
        df.drop('index', axis=1, inplace=True)
        
    # Columns from multiindex will not be parsed correctly
    if new_col_names:
        cols = new_col_names
    else:
        cols = df.columns.tolist()
    
    cols_w = [len(c)+ 2*col_pad for c in cols]
    
    if squeeze_factor == 0:
        squeeze_factor = 7.
        
    min_width = np.max(cols_w) #/ squeeze_factor  # previously 6.4
    df_widths = np.array(cols_w) / squeeze_factor

    df_heights = np.array([row_height] * df.shape[0])

    if ax is None:
        W, H = (df_widths.sum(), df_heights.sum())
        fig = plt.figure(figsize=(W, H));

        ax = plt.subplot();
        ax.axis('off');
        plt.xticks([]);
        plt.yticks([]);

        mpl_table = ax.table(cellText=df.values,
                             colLabels=cols,
                             colWidths=df_widths,
                             loc='center',
                             bbox=bbox,
                             **kwargs);

    mpl_table.auto_set_font_size(False);
    mpl_table.set_fontsize(font_size);
    mpl_table.scale(1, df.shape[0]+1);
    #         scale(xscale, yscale):
    # Scale col widths by xscale, row heights by yscale.

    for k, cell in six.iteritems(mpl_table._cells):
        cell.set_edgecolor(None);

        if k[0] == 0:
            cell.set_facecolor(header_color);
            cell.set_text_props(weight='bold', color='k');
            #cell.set_height(row_height/2);
        else:
            cell.set_facecolor(row_colors[k[0]%len(row_colors)-1]);
            if k[1] <= header_columns:
                #cell.set_facecolor(header_color);
                cell.set_text_props(weight='bold',
                                    color='k');

    if len(save_tbl_name):
        save_tbl_name = save_tbl_name + '.' + fig_format
        plt.savefig(os.path.join(gc4settings.DIR_IMG, save_tbl_name),
                    format=fig_format,
                    transparent=True, bbox_inches='tight',
                    pad_inches=0.05);

    if not show:
        plt.close();
    else:
        return ax;


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# The following variables will be set on import:

DIR_GEO = gc4settings.DIR_GEO
DIR_IMG = gc4settings.DIR_IMG
DIR_SHP = gc4settings.DIR_SHP
DIR_HTML = gc4settings.DIR_HTML
DIR_RPT = gc4settings.DIR_RPT
NB_CSS = gc4settings.NB_CSS

gdf_nyc_counties = gpd.read_file(os.path.join(DIR_SHP, 'nybbwi.shp'),
                                 driver='shapefile')
gdf_boston = get_gdf_boston()

# NYC borough/counties boundaries with maritime portion:
# https://www1.nyc.gov/site/planning/data-maps/open-data/
#       districts-download-metadata.page
boro_to_county = {'Manhattan': 'New York',
                  'Staten Island': 'Richmond',
                  'Brooklyn': 'Kings',
                  'Bronx': 'Bronx',
                  'Queens': 'Queens'}

# Load the geocoding variables in the namespace:
geocs = gc4settings.geocs
colors_dict = gc4settings.colors_dict

query_lst = gc4settings.query_lst
print('\nPlaces queried, var query_lst:\n{}'.format(query_lst))

# Call to load API keys from environment file if found:
print('\nFetching API keys from environment file if found.')

GOOGLE_KEY = gc4settings.GOOGLE_KEY
AZURE_KEY = gc4settings.AZURE_KEY
W3W_dict = gc4settings.W3W_dict

if (AZURE_KEY is None):
    print('Azure API key not in .env')
elif (GOOGLE_KEY is None):
    print('Google API key not in .env')
elif list(W3W_dict.values()) == [None]*len(W3W_dict):
    print('W3W API keys not in .env')

print('Module import operations: COMPLETE.')
#################################################################

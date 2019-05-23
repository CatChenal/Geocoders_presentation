# To test access to AzureMaps w/Geopy -> HTTP 400 error, Bad Request
from geopy.geocoders import AzureMaps
import requests

AZK = GeoComp4.AZURE_KEY

query_lst = ['New York City, NY, USA',
 "Cleopatra's needle, Central Park, New York, NY, USA",
 'Bronx county, NY, USA',
 'Kings county, NY, USA',
 'New York county, NY, USA',
 'Queens county, NY, USA',
 'Richmond county, NY, USA',
 'Boston, MA, USA']


tout = 5
geodata = OrderedDict()

USE_GEOPY = False

for i, q in enumerate(query_lst):
    info_d = OrderedDict()

    if 'county' in q:
        place = q.split(' county, ')[0] + ' county'
    else:
        place = q.split(', ')[0]

    if USE_GEOPY:
        g = AzureMaps(subscription_key=AZK,  domain='atlas.microsoft.com')
        location = g.geocode(q)
        #r = g.geocode('New York county, NY, USA')
        #r.raw['viewport']

    else:
        url_Azure = 'https://atlas.microsoft.com/search/address/json'
        params = {'subscription-key': AZK,
                  'api-version': 1.0,
                  'query': q,
                  'typeahead': False,
                  'limit': 1}
        r = requests.get(url_Azure, params=params)
        location = r.json()['results']
    
    if len(location):   # not sure that's a sufficient check...
        # bounding boxes as 2 corner pts: [NE], [SW]
        # Note: for locations West of GMT; adjustment needed otherwise
        info_d['loc'] = [location[0]['position']['lat'],
                         location[0]['position']['lon']]
        info_d['box'] = [[location[0]['viewport']['topLeftPoint']['lat'],
                          location[0]['viewport']['btmRightPoint']['lon']],
                         [location[0]['viewport']['btmRightPoint']['lat'],
                          location[0]['viewport']['topLeftPoint']['lon']] ]

    geodata[place] = info_d

    # save file (overwrite=default)
    out = 'geodata_Azu'
    DIR_GEO = os.path.join(Path('.'), 'geodata')
    out = os.path.join(DIR_GEO, out)
    GeoComp4.save_file(out, 'json', geodata)

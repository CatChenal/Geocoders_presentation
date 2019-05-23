old readme

# Comparison of Four Geocoders: Nominatim, GoogleV3, ArcGis and AzureMaps

## Geocoding services (via Geopy):

Obtaining the geolocation coordinates of a location specified by query string can be achieved using calls to geocoding APIs directly in a browser address box, or with
a wrapping library such as [geopy](https://geopy.readthedocs.io/en/stable/).

#### Here are the links to the geocoders geopy documentation and their respective service providers:
*  [**Nominatim**](https://wiki.openstreetmap.org/wiki/Nominatim): [OpenStreetMaps](https://wiki.openstreetmap.org/wiki/Using_OpenStreetMap)
*  [GoogleV3](https://geopy.readthedocs.io/en/stable/#googlev3): [Google Map & Places API](https://developers.google.com/maps/documentation/geocoding/start)
*  [ArcGis](https://geopy.readthedocs.io/en/stable/#ArcGis): [ERSI ArcGIS API](https://developers.arcgis.com/rest/geocode/api-reference/overview-world-geocoding-service.htm)
*  [AzureMaps](https://geopy.readthedocs.io/en/stable/#azuremaps): [Microsoft Azure Maps API](https://docs.microsoft.com/en-us/azure/azure-maps/index)

## Why I setup this comparison:
In another application, I was using the New York City boroughs bounding boxes to impute missing borough names for records with geolocation information (via set operations). 
The most expert GIS users among you would certainly predict scattershot results from such a "corner-cutting" approach, but initially I thought mine was a great way to prevent over 85,000 requests... Until I found out about the official territorial boundaries (shapefiles): then I trashed the box solution!  

Yet, in the intervening time I had checked several services for speed and limits and I found out response differences between some geocoders...for the same query, so I investigated!

The [**Procedures notebook**](./notebooks/GeocodersComparison/Procedures.ipynb) shows how to retrieve the data and call the functions.


## Shapefile sources:
* [New York City](https://data.cityofnewyork.us/City-Government/Borough-Boundaries-Water-Areas-Included-/tv64-9x69)
* [Boston](https://data.boston.gov/dataset/city-of-boston-boundary2)  


Because I noticed that the results from this April were different from those from last September (2018), I put together an HTML report highlighting the differences.

## Here is the updated report:  
I've implemented the "sliderReport.html" by modifying a ["JS-less CSS slider"](https://github.com/drygiel/csslider) designed by GH user drygiel"  
Thank you, drygiel!

<a href="https://catchenal.github.io/assets/sliderReport.html" target="_blank">Slider Report</a>


# The main conclusion from this comparison:

* Who is the best of all four?
 1. **Nominatim**: Star of the glorious open-source community (see the data on Cleopatra's Needle in Central Park);
 2. **GoogleV3**: not OS, but similar results to Nominatim
 3. ArcGis: the least wrong of the worse two
 4. AzureMaps: Oh come on! &#128534;

* No hedging!
I presume that it is very unlikely that an application would use different geolocating services, but in the case some 'hedging' is involved (e.g. on limits, time-outs), the geolocation for the same query will be different.

* Mind the box!
Additionally, my non-exhaustive comparison of four Geopy geocoders (out of 21), reveals that the boxing of a location is not always principled. For instance, Nominatim and GoogleV3 most often use the shapefile with water extent for boxing, whereas ArcGis and AzureMaps do not; moreover, ArcGis boxes typically extend further North than warranted by the existing shapefiles by at most 10 miles.    


Out of curiousity, I wonder how AzureMaps would fare against all geocoders...  

Speaking of which:  
At the time of this report, **April 2019**, there are 21 geocoding services available in geopy (excluding What3Words):  

The number of pairwise comparisons needed is 210.
This would require **51 more reports like this one**, which uses the python code in GeocoderComparison that compares only four geocoders.


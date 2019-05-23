import pytest
import sys

from .context import GeocodersComparison


# INC: also needed test values
"""
geocoder_to_use = 'GoogleV3'

geocs = ['Nominatim', 'GoogleV3', 'ArcGis', 'AzureMaps']
idx = geocs.index(geocoder_to_use) 


def get_geocoder(idx, tout=5):
    if idx == 0:
        return Nominatim(user_agent='this_app', country_bias='USA', timeout = tout)
    elif idx == 1:
        return GoogleV3(api_key=GOOGLE_KEY, timeout = tout)
    elif idx == 2:
        return ArcGIS(username=None, password=None, referer=None, user_agent='this_app', timeout=tout)
    else:
        return AzureMaps(subscription_key=AZURE_KEY, timeout=tout, user_agent='ths_app', domain='atlas.microsoft.com')
  

def compare_check0(geos=geo_dicts1, locale='New York City', which='box'):
    print('Check1:', 'geos_dicts1', locale, which, '\n')
    # wrong comparision type, which
    
    try:
        df = compare_3_geocoords(geos, place=locale, which_comparison=which)
        print('\tPass')
        return df
    except KeyError:
        print('KeyError with geo_dicts and locale combination.')
    except ValueError:
        print('Expected ValueError with wrong which arg')
    except Exception:
        print('Unexpected Exception error: investigate')
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise


def compare_check1(geos=geo_dicts1, locale='New York City', which='bounds'):
    print('Check1:', 'geos_dicts1', locale, which, '\n')
    
    try:
        df = compare_3_geocoords(geos, place=locale, which_comparison=which)
        print('\tPass')
        return df
    except KeyError:
        print('KeyError with geo_dicts and locale combination.')
    except ValueError:
        print('Expected ValueError with wrong which arg')
    except Exception:
        print('Unexpected Exception error: investigate')
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
        
        
def compare_check2(geos=geo_dicts1, locale='New York', which='location'):
    print('Check2', 'geos_dicts1', locale, which, '\n')
    
    try:
        df = compare_3_geocoords(geos, place=locale, which_comparison=which)
        print('\tPass')
        return df
    except KeyError:
        print('KeyError with geo_dicts and locale combination.')
    except ValueError:
        print('Expected ValueError with wrong which arg')
    except Exception:
        print('Unexpected Exception error: investigate')
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
        
        
def compare_check3(geos=geo_dicts2, locale='Bronx', which='location'):
    print('Check3', 'geo_dicts2', locale, which, '\n')

    try:
        df = compare_3_geocoords(geos, place=locale, which_comparison=which)
        print('\tPass')
        return df
    except KeyError:
        print('KeyError with geo_dicts and locale combination.')
    except ValueError:
        print('Expected ValueError with wrong which arg')
    except Exception:
        print('Unexpected Exception error: investigate')
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise


def compare_check4(geos=geo_dicts2, locale='Staten Island', which='bounds'):
    # unless a geolocation request was made for this place, "SI" is not a county name -> KeyError
    print('Check4', 'geo_dicts2', locale, which, '\n')
    try:
        df = compare_3_geocoords(geos, place=locale, which_comparison=which)
        print('\tPass')
        return df
    except KeyError:
        print('KeyError with geo_dicts and locale combination.')
    except ValueError:
        print('Expected ValueError with wrong which arg')
    except Exception:
        print('Unexpected Exception error: investigate')
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise          
"""
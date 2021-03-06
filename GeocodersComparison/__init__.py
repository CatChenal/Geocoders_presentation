name = 'GeocodersComparison'

__author__ = 'catchenal@gmail.com'

__all__ = ['gc4settings', 'gc4utils', 'comparison']


import os
from dotenv import find_dotenv

dot_env_path = find_dotenv()

if dot_env_path:
    __path__ = [os.path.join(os.path.dirname(dot_env_path), name)]

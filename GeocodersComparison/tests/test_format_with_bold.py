import pytest
import sys

from .context import GeocodersComparison

from GeocodersComparison import gc4utils

def test_format_with_bold(s_format):
    # remove trailing marker(s):
    s_format = s_format.replace('b_','')
    return gc4utils.format_with_bold(s_format)
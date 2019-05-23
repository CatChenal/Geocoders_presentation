# -*- coding: utf-8 -*-
"""
Mostly file & string processing routines, many
from Python Cookbook with additional docs & examples.

Naming conventions:
  Functions: underscore
  Classes: titlecase

@module: catutils.py
"""
__author__ = 'catchenal@gmail.com'

import os
import itertools
import string
import re


# String of all characters as a no-translation table:
allchars = string.maketrans('', '')

def make_filter(keep):
    """
    Return a function that takes a string & returns a partial copy
    consisting of the chars in keep (a plain string).
    Examples:
    vowels_only = make_filter('aeiou')
    print(vowels_only('tiger cat boom bam'))
    """
    # get set complement of keep -> delete
    delchars = allchars.translate(allchars, keep)
    
    def filter_str(s):
        return s.translate(allchars, delchars)
    
    return filter_str


class MakeFilter():
    """
    Like make_filter() for unicode strings.
    Example:
    filtering = MakeFilter()
    vowels_only = filtering('aeiou')
    print(vowels_only('tiger cat boom bam'))
    """
    
    def __init__(self, keep):
        self.keep = set(map(ord, keep))
        
    def __getitem__(self, n):
        if n not in self.keep:
            return None
        return unichar(n)
    
    def __call__(self, s):
        return unicode(s).translate(self)
    
    
def contains_any(seq, aset):
    """ Check whether sequence seq contains any of the items in a set."""
    for item in itertools.ifilter(aset.__contains__, seq):
        return True
    return False


def contains_all(seq, aset):
    """ Check whether sequence seq contains all of the items in a set."""
    return not set(aset).difference(seq)


def translator(frm='', to='', delete='', keep=None):
    """
    Example:
    digits_only = translator(keep=string.digits)
    digits_from_field = digits_only('Some name: 293297-7')
    # converse:
    np_digits = translator(delete=string.digits)
    text_from_field = no_digits('Some name: 293297-7')
    # masking:
    mask_digits = translator(frm=string.digits, to='*')
    text_with_masked_id = maskdigits('Some name: 293297-7')
    """
    if len(to) == 1:
        to *= len(frm)
    
    trans = string.maketrans(frm, to)
    
    if keep in not None:
        delete = allchars.translate(allchars,
                                    keep.translate(allchars, delete))
        
    def _translate(s):
        return s.translate(trans, delete)
    
    return _translate


def as_of():
    import datetime
    return datetime.datetime.today().strftime("%b %Y")


def caveat_codor():
    import sys
    from IPython.display import Markdown

    mysys = '{} | {}<br>As of:  {}'.format(sys.version,
                                           sys.platform,
                                           as_of())
    msg = "The code and information herein is valid given my "
    msg += "understanding and this environment:<br>"
    return Markdown(msg + mysys)


def get_file_ext(path, max_multi_ext=2):
    """max_multi_ext enables common double extensions 
       such as '.tar.gz'
    """
    p = os.path.basename(path)
    if len(p.split('.')) > 2:
        return '.'.join(p.split('.')[-max_multi_ext:])
    return os.path.splitext(p)[1]


def save_file(fname, ext, s, replace=True):
    # check if fname has an extension:
    x = get_file_ext(fname)
    
    if x:
        outfile = fname.split(x)[0] + '.' + ext
    else:
        outfile = fname + '.' + ext
    
    if replace:
        if os.path.exists(outfile):
            os.remove(outfile)

    if isinstance(s, dict):
        import json

        with open(outfile, 'w') as fw:
            json.dump(s, fw)
    else:
        if len(s):
            with open(outfile, 'w') as f:
                f.write(s)
    return


def get_file_age(fullfilename):
    """
    To be called after a file existence check.
    Returns a string.
    """
    from datetime import datetime
    
    if not isinstance(fullfilename, str):
        return ''

    diff = datetime.utcnow()
    try:
        diff -= datetime.utcfromtimestamp(os.stat(fullfilename).st_atime)
    except:
        return ''

    dd = str(diff).split(':')
    info = ': {}, {}h {}m {:.0f}s old'.format( fullfilename,
                                                         dd[0], dd[1],
                                                         float(dd[2]))
    return info

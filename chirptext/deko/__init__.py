# -*- coding: utf-8 -*-

"""
Convenient Japanese text parser that produces results in TTL format
"""

# Reference
#   - MeCab homepage: http://taku910.github.io/mecab/
#
# MeCab, デコ, got the joke?
# This script was adopted from https://github.com/letuananh/omwtk
#
# This code is a part of chirptext library: https://github.com/letuananh/chirptext
# :copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

from . import mecab
from . import util

# allow mecab config
set_mecab_bin = mecab._register_mecab_loc
get_mecab_bin = mecab._get_mecab_loc
parse = mecab.parse
parse_doc = mecab.parse_doc
tokenize = mecab.tokenize
tokenize_sent = mecab.tokenize_sent


def analyse(content, splitlines=True, format=None, **kwargs):
    """ Japanese text > tokenize/txt/html """
    doc = parse_doc(content, splitlines=splitlines, **kwargs)
    output_text = []
    final = doc
    # Generate output
    if format == 'html':
        for sent in doc:
            output_text.append(util.sent_to_ruby(sent))
        final = '<br/>\n'.join(output_text)
    elif format == 'csv':
        for sent in doc:
            output_text.append(util.to_csv(sent))
            output_text.append('\n')
        final = '\n'.join(output_text)
    elif format == 'txt':
        final = '\n'.join((' '.join(tk.text for tk in sent) for sent in doc))
    return final


__all__ = ['set_mecab_bin', 'get_mecab_bin',
           'parse', 'parse_doc', 'tokenize', 'tokenize_sent', 'analyse']



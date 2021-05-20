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
from . import dekoigo
from . import janome
from . import util
from .util import kata2hira, is_kana, HIRAGANA, KATAKANA

# allow mecab config
set_mecab_bin = mecab._register_mecab_loc
get_mecab_bin = mecab._get_mecab_loc


def engines():
    _engines = []
    try:
        mv = mecab.version()
        if mv:
            _engines.append(("mecab", mecab))
    except Exception:
        pass
    if dekoigo.igo_available():
        _engines.append(("igo", dekoigo))
    if janome.janome_available():
        _engines.append(("janome", dekoigo))
    return _engines


def _locate_engine(*args, **kwargs):
    _engines = engines()
    if not _engines:
        raise RuntimeError("There is no Japanese parser available")
    else:
        return _engines[0][1]


def parse(*args, **kwargs):
    return _locate_engine().parse(*args, **kwargs)


def parse_doc(*args, **kwargs):
    return _locate_engine().parse_doc(*args, **kwargs)


def tokenize(*args, **kwargs):
    return _locate_engine().tokenize(*args, **kwargs)


def tokenize_sent(*args, **kwargs):
    return _locate_engine().tokenize_sent(*args, **kwargs)


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


__all__ = ['set_mecab_bin', 'get_mecab_bin', 'engines',
           'parse', 'parse_doc', 'tokenize', 'tokenize_sent', 'analyse']


